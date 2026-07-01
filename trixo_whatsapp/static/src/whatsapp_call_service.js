/** @odoo-module **/
// Trixocom — Aviso de llamada WhatsApp entrante (F5, primera pieza).
// Escucha el bus ("whatsapp.call", empujado por whatsapp.account._notify_call_bus)
// y muestra una notificación prominente + beep, como aviso visible de llamada.
// Atender/hablar en vivo llega con el puente de audio (F4) y el softphone completo.

import { registry } from "@web/core/registry";

const RING_MS = 30000; // corta el beep solo por las dudas

export const whatsappCallService = {
    dependencies: ["bus_service", "notification"],
    start(env, { bus_service, notification }) {
        const active = new Map(); // call_id -> { close, stopRing }
        let audioCtx = null;

        function beepLoop() {
            // Beep suave y repetido con WebAudio (sin archivo). Best-effort:
            // el navegador puede bloquearlo hasta que haya interacción del usuario.
            try {
                audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
            } catch (e) {
                return () => {};
            }
            let stopped = false;
            const tick = () => {
                if (stopped || !audioCtx) {
                    return;
                }
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sine";
                osc.frequency.value = 880;
                gain.gain.value = 0.0001;
                osc.connect(gain).connect(audioCtx.destination);
                const t = audioCtx.currentTime;
                gain.gain.exponentialRampToValueAtTime(0.15, t + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
                osc.start(t);
                osc.stop(t + 0.42);
            };
            tick();
            const iv = setInterval(tick, 1500);
            const to = setTimeout(() => { stopped = true; clearInterval(iv); }, RING_MS);
            return () => { stopped = true; clearInterval(iv); clearTimeout(to); };
        }

        function dismiss(callId) {
            const entry = active.get(callId);
            if (entry) {
                entry.stopRing && entry.stopRing();
                entry.close && entry.close();
                active.delete(callId);
            }
        }

        bus_service.subscribe("whatsapp.call", (payload) => {
            if (!payload || !payload.call_id) {
                return;
            }
            const who = payload.partner_name || payload.phone_number || "Desconocido";
            const kind = payload.kind;

            if (kind === "incoming" || kind === "ringing") {
                if (active.has(payload.call_id)) {
                    return;
                }
                const stopRing = beepLoop();
                const close = notification.add(`📞 Llamada entrante de ${who}`, {
                    title: "WhatsApp",
                    type: "warning",
                    sticky: true,
                });
                active.set(payload.call_id, { close, stopRing });
            } else if (kind === "missed") {
                dismiss(payload.call_id);
                notification.add(`📞 Llamada perdida de ${who}`, {
                    title: "WhatsApp",
                    type: "danger",
                });
            } else {
                // ongoing / terminated / rejected / aborted -> quitar el aviso
                dismiss(payload.call_id);
            }
        });
        bus_service.start();
    },
};

registry.category("services").add("trixo_whatsapp_call", whatsappCallService);
