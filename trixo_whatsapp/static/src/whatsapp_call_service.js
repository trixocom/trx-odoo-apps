/** @odoo-module **/
// Trixocom — Softphone WhatsApp. Ítem de systray (barra superior, estilo Enterprise
// voip) + panel de llamada (invitación Aceptar/Rechazar, en-llamada con timer, dialer)
// + audio en vivo full-duplex por WebSocket al sidecar (resample 48k<->16k). El botón
// del systray es OWL (mínimo); el panel es DOM plano y defensivo para no romper el
// backend. Ring persistente con WebAudio (resume por gesto del usuario).

import { Component, xml, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Estado compartido systray <-> lógica (module scope).
const sp = {
    ringing: false,
    inCall: false,
    missed: 0,
    open: false,
    openDialer: () => {},
    version: 0, // bump para forzar re-render del systray
};
const listeners = new Set();
function notifyUI() { sp.version++; listeners.forEach((f) => f()); }

// ---------------- util audio ----------------
function resampleFloat(data, from, to) {
    if (from === to || !data.length) return data;
    const ratio = from / to;
    const n = Math.max(1, Math.floor(data.length / ratio));
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) {
        const idx = i * ratio, i0 = Math.floor(idx), frac = idx - i0;
        const a = data[i0] || 0, b = (i0 + 1 < data.length ? data[i0 + 1] : a);
        out[i] = a + (b - a) * frac;
    }
    return out;
}
function floatToS16(f) {
    const buf = new ArrayBuffer(f.length * 2);
    const dv = new DataView(buf);
    for (let i = 0; i < f.length; i++) {
        let v = Math.max(-1, Math.min(1, f[i])) * 32767;
        dv.setInt16(i * 2, v, true);
    }
    return buf;
}
function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function initials(s) {
    const p = String(s || "?").trim().split(/\s+/);
    return ((p[0] || "")[0] || "?").toUpperCase() + ((p[1] || "")[0] || "").toUpperCase();
}

export const whatsappCallService = {
    dependencies: ["bus_service", "orm", "notification"],
    start(env, { bus_service, orm, notification }) {
        try { startSoftphone(env, { bus_service, orm, notification }); }
        catch (e) { console.error("[trixo_whatsapp] softphone init", e); }
    },
};

function startSoftphone(env, { bus_service, orm, notification }) {
    injectStyles();
    const root = document.createElement("div");
    root.className = "twa-sp-root";
    document.body.appendChild(root);

    let current = null;
    let timerIv = null, timerStart = 0;
    let audio = null;

    // ---------- audio context compartido + ring ----------
    let actx = null;
    function ensureCtx() {
        try {
            actx = actx || new (window.AudioContext || window.webkitAudioContext)();
            if (actx.state === "suspended") { actx.resume().catch(() => {}); }
        } catch (e) { actx = null; }
        return actx;
    }
    // "prime" el audio con cualquier gesto del usuario (política de autoplay).
    window.addEventListener("pointerdown", () => ensureCtx(), { capture: true });

    let ringIv = null;
    function startRing() {
        stopRing();
        const ctx = ensureCtx();
        if (!ctx) return;
        const pattern = () => {
            if (!ctx) return;
            // doble tono tipo "ring ring"
            beep(ctx, 480, ctx.currentTime, 0.4);
            beep(ctx, 440, ctx.currentTime + 0.45, 0.4);
        };
        pattern();
        ringIv = setInterval(pattern, 2200);
    }
    function stopRing() { if (ringIv) { clearInterval(ringIv); ringIv = null; } }
    function beep(ctx, freq, t, dur) {
        try {
            const osc = ctx.createOscillator(), g = ctx.createGain();
            osc.type = "sine"; osc.frequency.value = freq; g.gain.value = 0.0001;
            osc.connect(g).connect(ctx.destination);
            g.gain.exponentialRampToValueAtTime(0.2, t + 0.03);
            g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
            osc.start(t); osc.stop(t + dur + 0.02);
        } catch (e) {}
    }

    // ---------- audio en vivo ----------
    async function connectAudio(recordId, callId) {
        if (audio && audio.callId === callId) return;
        disconnectAudio();
        let creds;
        try { creds = await orm.call("whatsapp.call", "audio_credentials", [[recordId]]); }
        catch (e) { console.error("[trixo_whatsapp] audio_credentials", e); return; }
        if (!creds || !creds.url) return;
        const wsUrl = creds.url + "?call_id=" + encodeURIComponent(callId) + "&token=" + encodeURIComponent(creds.token);
        let stream;
        try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
        catch (e) { notify("Sin acceso al micrófono", "danger"); return; }
        const ctx = ensureCtx();
        if (!ctx) { stream.getTracks().forEach((t) => t.stop()); return; }
        const inRate = ctx.sampleRate || 48000;
        const ws = new WebSocket(wsUrl);
        ws.binaryType = "arraybuffer";
        let playBuf = new Float32Array(0);
        const srcNode = ctx.createMediaStreamSource(stream);
        const node = ctx.createScriptProcessor(4096, 1, 1);
        node.onaudioprocess = (e) => {
            try {
                const input = e.inputBuffer.getChannelData(0);
                const down = resampleFloat(input, inRate, 16000);
                if (ws.readyState === 1) ws.send(floatToS16(down));
                const out = e.outputBuffer.getChannelData(0);
                const take = Math.min(out.length, playBuf.length);
                for (let i = 0; i < out.length; i++) out[i] = i < take ? playBuf[i] : 0;
                playBuf = playBuf.subarray(take);
            } catch (err) {}
        };
        ws.onmessage = (ev) => {
            try {
                const s16 = new Int16Array(ev.data);
                const f = new Float32Array(s16.length);
                for (let i = 0; i < s16.length; i++) f[i] = s16[i] / 32768;
                const up = resampleFloat(f, 16000, inRate);
                const nb = new Float32Array(playBuf.length + up.length);
                nb.set(playBuf); nb.set(up, playBuf.length);
                playBuf = nb.length > inRate ? nb.subarray(nb.length - inRate) : nb;
            } catch (err) {}
        };
        srcNode.connect(node); node.connect(ctx.destination);
        audio = { ws, node, src: srcNode, stream, callId };
    }
    function disconnectAudio() {
        if (!audio) return;
        try { audio.node.disconnect(); } catch (e) {}
        try { audio.src.disconnect(); } catch (e) {}
        try { audio.ws.close(); } catch (e) {}
        try { audio.stream.getTracks().forEach((t) => t.stop()); } catch (e) {}
        audio = null;
    }

    // ---------- helpers UI ----------
    function notify(m, t) { try { notification.add(m, { title: "WhatsApp", type: t || "info" }); } catch (e) {} }
    async function ormCall(model, method, args) {
        try { return await orm.call(model, method, args); }
        catch (e) { console.error("[trixo_whatsapp]", method, e); notify("Error: " + (e.message || method), "danger"); }
    }
    function clearTimer() { if (timerIv) { clearInterval(timerIv); timerIv = null; } }
    function startTimer() {
        clearTimer(); timerStart = Date.now();
        const upd = () => {
            const el = root.querySelector("#twa-timer"); if (!el) return;
            const s = Math.floor((Date.now() - timerStart) / 1000);
            el.textContent = (s / 60 | 0).toString().padStart(2, "0") + ":" + (s % 60).toString().padStart(2, "0");
        };
        upd(); timerIv = setInterval(upd, 500);
    }
    function close() {
        stopRing(); clearTimer(); disconnectAudio();
        current = null; sp.ringing = false; sp.inCall = false; sp.open = false;
        render(); notifyUI();
    }
    sp.openDialer = () => { sp.open = true; current = null; render(); notifyUI(); };

    // ---------- render panel (DOM plano) ----------
    function render() {
        if (current && current.ui === "incoming") return renderIncoming();
        if (current && current.ui === "incall") return renderInCall();
        if (sp.open) return renderDialer();
        root.innerHTML = "";
    }
    function avatarHtml(name) {
        return `<div class="twa-av">${escapeHtml(initials(name))}</div>`;
    }
    function shell(inner, extra) {
        root.innerHTML = `<div class="twa-card ${extra || ""}">${inner}</div>`;
    }
    function renderDialer() {
        shell(`
          <div class="twa-hd"><span>Llamar por WhatsApp</span>
            <button class="twa-x" title="Cerrar">&times;</button></div>
          <div class="twa-bd">
            <input class="twa-inp" placeholder="Número (ej: 5491169745243)" inputmode="tel"/>
            <button class="twa-btn twa-green twa-dial"><i class="fa fa-phone"></i> Llamar</button>
          </div>`);
        const inp = root.querySelector(".twa-inp");
        setTimeout(() => inp && inp.focus(), 40);
        root.querySelector(".twa-x").onclick = () => { sp.open = false; render(); notifyUI(); };
        root.querySelector(".twa-dial").onclick = async () => {
            const num = (inp.value || "").trim(); if (!num) return;
            ensureCtx();
            const res = await ormCall("whatsapp.account", "softphone_place", [num]);
            if (res) {
                current = { ui: "incall", id: res.id, call_id: res.call_id,
                            who: res.partner_name || res.phone_number || num, direction: "outgoing", label: "Llamando…" };
                sp.open = false; sp.inCall = true;
                render(); startTimer(); notifyUI();
                connectAudio(res.id, res.call_id);
            }
        };
    }
    function renderIncoming() {
        shell(`
          <div class="twa-sub">Llamada WhatsApp entrante</div>
          ${avatarHtml(current.who)}
          <div class="twa-name">${escapeHtml(current.who)}</div>
          <div class="twa-num">${escapeHtml(current.number || "")}</div>
          <div class="twa-actions">
            <button class="twa-round twa-red twa-reject" title="Rechazar"><i class="fa fa-close"></i></button>
            <button class="twa-round twa-green twa-answer" title="Atender"><i class="fa fa-phone"></i></button>
          </div>`, "twa-ring");
        root.querySelector(".twa-answer").onclick = async () => {
            ensureCtx(); stopRing(); sp.ringing = false;
            current.ui = "incall"; current.label = "En llamada"; sp.inCall = true;
            render(); startTimer(); notifyUI();
            await ormCall("whatsapp.call", "action_answer", [[current.id]]);
            connectAudio(current.id, current.call_id);
        };
        root.querySelector(".twa-reject").onclick = async () => {
            await ormCall("whatsapp.call", "action_reject", [[current.id]]); close();
        };
    }
    function renderInCall() {
        shell(`
          <div class="twa-sub">${escapeHtml(current.label || "En llamada")}</div>
          ${avatarHtml(current.who)}
          <div class="twa-name">${escapeHtml(current.who)}</div>
          <div class="twa-timer" id="twa-timer">00:00</div>
          <div class="twa-actions">
            <button class="twa-round twa-red twa-hangup" title="Colgar"><i class="fa fa-phone"></i></button>
          </div>`, "twa-active");
        root.querySelector(".twa-hangup").onclick = async () => {
            await ormCall("whatsapp.call", "action_hangup", [[current.id]]); close();
        };
    }

    // ---------- bus ----------
    bus_service.subscribe("whatsapp.call", (p) => {
        try {
            if (!p || !p.call_id) return;
            const who = p.partner_name || p.phone_number || "Desconocido";
            const kind = p.kind;
            if (kind === "incoming" || (kind === "ringing" && p.direction === "incoming")) {
                current = { ui: "incoming", id: p.id, call_id: p.call_id, who, number: p.phone_number, direction: "incoming" };
                sp.ringing = true; sp.open = false;
                render(); startRing(); notifyUI();
            } else if (kind === "ongoing") {
                if (current && current.call_id === p.call_id) {
                    current.ui = "incall"; current.label = "En llamada"; sp.inCall = true; sp.ringing = false;
                    render(); startTimer(); notifyUI();
                    connectAudio(current.id, current.call_id);
                }
            } else if (kind === "missed") {
                sp.missed++; notify("📞 Llamada perdida de " + who, "warning"); close();
            } else if (["terminated", "rejected", "aborted"].includes(kind)) {
                if (current && current.call_id === p.call_id) close();
            }
        } catch (e) { console.error("[trixo_whatsapp] bus", e); }
    });
    bus_service.start();
}

// ---------------- OWL systray item (barra superior) ----------------
class WhatsAppSystray extends Component {
    static template = xml`
      <div class="o-dropdown dropdown o_dropdown">
        <button class="o_nav_entry btn" t-att-class="{ 'text-success': state.ringing, 'text-primary': state.inCall }"
                t-att-title="title" t-on-click="onClick">
          <i class="fa fa-phone" t-att-class="{ 'twa-ring-icon': state.ringing }"/>
          <span t-if="state.missed" class="badge rounded-pill text-bg-danger ms-1" t-esc="state.missed"/>
        </button>
      </div>`;
    setup() {
        this.state = useState({ ringing: false, inCall: false, missed: 0 });
        const sync = () => {
            this.state.ringing = sp.ringing;
            this.state.inCall = sp.inCall;
            this.state.missed = sp.missed;
        };
        listeners.add(sync); sync();
    }
    get title() { return this.state.inCall ? "En llamada WhatsApp" : "Softphone WhatsApp"; }
    onClick() {
        sp.missed = 0;
        try { sp.openDialer(); } catch (e) {}
        this.state.missed = 0;
    }
}
registry.category("systray").add("trixo_whatsapp_call", { Component: WhatsAppSystray }, { sequence: 90 });

registry.category("services").add("trixo_whatsapp_call", whatsappCallService);

// ---------------- estilos ----------------
function injectStyles() {
    if (document.getElementById("twa-sp-style")) return;
    const s = document.createElement("style");
    s.id = "twa-sp-style";
    s.textContent = `
    .twa-sp-root{position:fixed;left:16px;bottom:16px;z-index:1050;font-family:inherit}
    .twa-card{width:300px;background:var(--o-view-background-color,#fff);color:#111;border:1px solid rgba(0,0,0,.12);border-radius:12px;box-shadow:0 12px 40px rgba(0,0,0,.28);padding:18px;text-align:center}
    .twa-hd{display:flex;align-items:center;justify-content:space-between;font-weight:600;margin-bottom:12px}
    .twa-x{border:none;background:none;font-size:20px;line-height:1;cursor:pointer;color:#888}
    .twa-bd{display:flex;flex-direction:column;gap:10px}
    .twa-inp{width:100%;box-sizing:border-box;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:15px}
    .twa-sub{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:#8a8a8a}
    .twa-av{width:64px;height:64px;border-radius:50%;margin:12px auto 6px;background:#25D366;color:#fff;font-size:24px;font-weight:700;display:flex;align-items:center;justify-content:center}
    .twa-name{font-size:19px;font-weight:700}
    .twa-num{font-size:13px;color:#8a8a8a;margin-bottom:6px}
    .twa-timer{font-size:22px;font-weight:700;color:#25D366;margin:8px 0}
    .twa-actions{display:flex;gap:26px;justify-content:center;margin-top:14px}
    .twa-round{width:56px;height:56px;border-radius:50%;border:none;color:#fff;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center}
    .twa-green{background:#25D366}.twa-red{background:#e53935}
    .twa-red .fa-phone{transform:rotate(135deg)}
    .twa-round:hover{filter:brightness(1.08)}
    .twa-btn{padding:11px;border:none;border-radius:9px;color:#fff;font-weight:600;cursor:pointer;font-size:14px}
    .twa-ring{animation:twaPulse 1.1s infinite}
    .twa-ring-icon{animation:twaShake .8s infinite}
    @keyframes twaPulse{0%,100%{box-shadow:0 12px 40px rgba(37,211,102,.15)}50%{box-shadow:0 12px 48px rgba(37,211,102,.6)}}
    @keyframes twaShake{0%,100%{transform:rotate(0)}25%{transform:rotate(-15deg)}75%{transform:rotate(15deg)}}
    `;
    document.head.appendChild(s);
}
