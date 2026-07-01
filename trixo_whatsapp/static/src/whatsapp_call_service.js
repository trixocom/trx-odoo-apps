/** @odoo-module **/
// Trixocom — Softphone WhatsApp (F5 UI + F4 audio en vivo).
// Escucha el bus ("whatsapp.call") y muestra el softphone: entrante con Atender/
// Rechazar, barra en-llamada con timer + Colgar, dialer para marcar. Cuando la
// llamada pasa a activa abre un WebSocket de audio al sidecar y hace full-duplex
// (mic del navegador <-> audio del peer) resampleando 48k<->16k. DOM plano y todo
// en try/catch: si algo falla queda contenido y no rompe el backend de Odoo.

import { registry } from "@web/core/registry";

const RING_MS = 45000;

export const whatsappCallService = {
    dependencies: ["bus_service", "orm", "notification"],
    start(env, { bus_service, orm, notification }) {
        try {
            return startSoftphone(env, { bus_service, orm, notification });
        } catch (e) {
            console.error("[trixo_whatsapp] softphone init error", e);
        }
    },
};

function startSoftphone(env, { bus_service, orm, notification }) {
    injectStyles();
    const root = el("div", "twa-sp-root");
    document.body.appendChild(root);

    let current = null;
    let stopRing = null;
    let timerIv = null;
    let audio = null; // { ws, ctx, node, src, stream }

    // ---------------- beep ----------------
    let audioCtx = null;
    function beepLoop() {
        try {
            audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) { return () => {}; }
        let stopped = false;
        const tick = () => {
            if (stopped || !audioCtx) return;
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = "sine"; osc.frequency.value = 880; gain.gain.value = 0.0001;
            osc.connect(gain).connect(audioCtx.destination);
            const t = audioCtx.currentTime;
            gain.gain.exponentialRampToValueAtTime(0.15, t + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
            osc.start(t); osc.stop(t + 0.42);
        };
        tick();
        const iv = setInterval(tick, 1500);
        const to = setTimeout(() => { stopped = true; clearInterval(iv); }, RING_MS);
        return () => { stopped = true; clearInterval(iv); clearTimeout(to); };
    }
    function stopBeep() { if (stopRing) { try { stopRing(); } catch (e) {} stopRing = null; } }

    // ---------------- audio en vivo (F4) ----------------
    async function connectAudio(recordId, callId) {
        if (audio && audio.callId === callId) return;
        disconnectAudio();
        let creds;
        try { creds = await orm.call("whatsapp.call", "audio_credentials", [[recordId]]); }
        catch (e) { console.error("[trixo_whatsapp] audio_credentials", e); return; }
        if (!creds || !creds.url) { console.warn("[trixo_whatsapp] sin credenciales de audio"); return; }
        const wsUrl = creds.url + "?call_id=" + encodeURIComponent(callId) +
                      "&token=" + encodeURIComponent(creds.token);
        let stream;
        try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
        catch (e) { notify("Sin acceso al micrófono", "danger"); return; }
        let ctx;
        try {
            ctx = new (window.AudioContext || window.webkitAudioContext)();
            if (ctx.state === "suspended") { try { await ctx.resume(); } catch (e) {} }
        } catch (e) { stream.getTracks().forEach((t) => t.stop()); return; }
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
                const n = out.length;
                const take = Math.min(n, playBuf.length);
                for (let i = 0; i < n; i++) out[i] = i < take ? playBuf[i] : 0;
                playBuf = playBuf.subarray(take);
            } catch (err) { /* nunca romper el audio loop */ }
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
        ws.onerror = () => console.warn("[trixo_whatsapp] audio WS error");
        srcNode.connect(node); node.connect(ctx.destination);
        audio = { ws, ctx, node, src: srcNode, stream, callId };
        console.log("[trixo_whatsapp] audio conectado", inRate);
    }
    function disconnectAudio() {
        if (!audio) return;
        try { audio.node.disconnect(); } catch (e) {}
        try { audio.src.disconnect(); } catch (e) {}
        try { audio.ws.close(); } catch (e) {}
        try { audio.stream.getTracks().forEach((t) => t.stop()); } catch (e) {}
        try { audio.ctx.close(); } catch (e) {}
        audio = null;
    }

    // ---------------- helpers ----------------
    function clearTimer() { if (timerIv) { clearInterval(timerIv); timerIv = null; } }
    function fmt(sec) {
        const m = Math.floor(sec / 60), s = sec % 60;
        return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
    }
    function clearCard() {
        stopBeep(); clearTimer(); disconnectAudio();
        root.innerHTML = renderLauncher(); bindLauncher(); current = null;
    }
    function notify(msg, type) { try { notification.add(msg, { title: "WhatsApp", type: type || "info" }); } catch (e) {} }
    async function ormCall(model, method, args) {
        try { return await orm.call(model, method, args); }
        catch (e) { console.error("[trixo_whatsapp] orm", method, e); notify("Error: " + (e.message || method), "danger"); }
    }

    // ---------------- render ----------------
    function renderLauncher() { return `<button class="twa-sp-launch" title="Marcar por WhatsApp">📞</button>`; }
    function bindLauncher() { const b = root.querySelector(".twa-sp-launch"); if (b) b.onclick = openDialer; }
    function openDialer() {
        root.innerHTML = `
          <div class="twa-sp-card">
            <div class="twa-sp-head">Llamar por WhatsApp</div>
            <input class="twa-sp-input" placeholder="Número (ej: 5491169745243)" inputmode="tel"/>
            <div class="twa-sp-row">
              <button class="twa-sp-btn twa-sp-green twa-dial">Llamar</button>
              <button class="twa-sp-btn twa-sp-grey twa-close">Cerrar</button>
            </div>
          </div>`;
        const inp = root.querySelector(".twa-sp-input");
        setTimeout(() => inp && inp.focus(), 50);
        root.querySelector(".twa-close").onclick = clearCard;
        root.querySelector(".twa-dial").onclick = async () => {
            const num = (inp.value || "").trim();
            if (!num) return;
            const res = await ormCall("whatsapp.account", "softphone_place", [num]);
            if (res) {
                current = { call_id: res.call_id, id: res.id, state: "calling",
                            who: res.partner_name || res.phone_number || num, direction: "outgoing" };
                renderActive("Llamando…");
                connectAudio(res.id, res.call_id);
            }
        };
    }
    function renderIncoming(p) {
        stopBeep(); stopRing = beepLoop();
        root.innerHTML = `
          <div class="twa-sp-card twa-ring">
            <div class="twa-sp-sub">Llamada entrante</div>
            <div class="twa-sp-who">${escapeHtml(p.who)}</div>
            <div class="twa-sp-num">${escapeHtml(p.number || "")}</div>
            <div class="twa-sp-row">
              <button class="twa-sp-btn twa-sp-green twa-answer">Atender</button>
              <button class="twa-sp-btn twa-sp-red twa-reject">Rechazar</button>
            </div>
          </div>`;
        root.querySelector(".twa-answer").onclick = async () => {
            stopBeep(); renderActive("En llamada"); startTimer();
            await ormCall("whatsapp.call", "action_answer", [[p.id]]);
            connectAudio(p.id, p.call_id);
        };
        root.querySelector(".twa-reject").onclick = async () => {
            await ormCall("whatsapp.call", "action_reject", [[p.id]]); clearCard();
        };
    }
    function renderActive(label) {
        if (!current) return;
        stopBeep();
        root.innerHTML = `
          <div class="twa-sp-card twa-active">
            <div class="twa-sp-sub">${escapeHtml(label || "En llamada")}</div>
            <div class="twa-sp-who">${escapeHtml(current.who)}</div>
            <div class="twa-sp-timer" id="twa-timer">00:00</div>
            <div class="twa-sp-row">
              <button class="twa-sp-btn twa-sp-red twa-hangup">Colgar</button>
            </div>
          </div>`;
        root.querySelector(".twa-hangup").onclick = async () => {
            await ormCall("whatsapp.call", "action_hangup", [[current.id]]); clearCard();
        };
    }
    function startTimer() {
        clearTimer(); let sec = 0;
        const set = () => { const t = root.querySelector("#twa-timer"); if (t) t.textContent = fmt(sec); };
        set(); timerIv = setInterval(() => { sec += 1; set(); }, 1000);
    }

    // ---------------- bus ----------------
    bus_service.subscribe("whatsapp.call", (p) => {
        try {
            if (!p || !p.call_id) return;
            const who = p.partner_name || p.phone_number || "Desconocido";
            const kind = p.kind;
            if (kind === "incoming" || (kind === "ringing" && p.direction === "incoming")) {
                current = { call_id: p.call_id, id: p.id, state: "ringing", who, number: p.phone_number, direction: "incoming" };
                renderIncoming(current);
            } else if (kind === "ongoing") {
                if (!current || current.call_id !== p.call_id) {
                    current = { call_id: p.call_id, id: p.id, who, direction: p.direction };
                }
                current.state = "ongoing";
                renderActive("En llamada"); startTimer();
                connectAudio(current.id, current.call_id);
            } else if (kind === "missed") {
                clearCard(); notify("📞 Llamada perdida de " + who, "warning");
            } else if (["terminated", "rejected", "aborted"].includes(kind)) {
                if (current && current.call_id === p.call_id) clearCard();
            }
        } catch (e) { console.error("[trixo_whatsapp] bus handler", e); }
    });
    bus_service.start();

    clearCard();
}

// ---------------- util ----------------
function el(tag, cls) { const e = document.createElement(tag); if (cls) e.className = cls; return e; }
function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
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
function injectStyles() {
    if (document.getElementById("twa-sp-style")) return;
    const s = document.createElement("style");
    s.id = "twa-sp-style";
    s.textContent = `
    .twa-sp-root{position:fixed;right:20px;bottom:20px;z-index:100000;font-family:inherit}
    .twa-sp-launch{width:56px;height:56px;border-radius:50%;border:none;background:#25D366;color:#fff;font-size:24px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25)}
    .twa-sp-launch:hover{filter:brightness(1.05)}
    .twa-sp-card{width:280px;background:#fff;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.28);padding:18px;text-align:center;border:1px solid #e6e6e6}
    .twa-sp-head{font-weight:600;margin-bottom:10px;color:#111}
    .twa-sp-sub{font-size:12px;color:#888;text-transform:uppercase;letter-spacing:.5px}
    .twa-sp-who{font-size:20px;font-weight:700;color:#111;margin:6px 0}
    .twa-sp-num{font-size:13px;color:#888;margin-bottom:12px}
    .twa-sp-timer{font-size:22px;font-weight:700;color:#25D366;margin:10px 0}
    .twa-sp-input{width:100%;box-sizing:border-box;padding:10px;border:1px solid #ccc;border-radius:8px;margin-bottom:12px;font-size:15px}
    .twa-sp-row{display:flex;gap:10px;justify-content:center}
    .twa-sp-btn{flex:1;padding:11px;border:none;border-radius:9px;color:#fff;font-weight:600;cursor:pointer;font-size:14px}
    .twa-sp-green{background:#25D366}.twa-sp-red{background:#e53935}.twa-sp-grey{background:#9e9e9e}
    .twa-sp-btn:hover{filter:brightness(1.06)}
    .twa-ring{animation:twaPulse 1.2s infinite}
    @keyframes twaPulse{0%{box-shadow:0 10px 30px rgba(37,211,102,.15)}50%{box-shadow:0 10px 40px rgba(37,211,102,.55)}100%{box-shadow:0 10px 30px rgba(37,211,102,.15)}}
    `;
    document.head.appendChild(s);
}

registry.category("services").add("trixo_whatsapp_call", whatsappCallService);
