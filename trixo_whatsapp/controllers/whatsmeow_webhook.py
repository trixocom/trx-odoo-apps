# Part of Trixocom.
"""Webhook entrante del sidecar WuzAPI (formato real, WEBHOOK_FORMAT=json).

Payload WuzAPI (evento whatsmeow crudo)::

    {
      "type": "Message",
      "instanceName": "<nombre del user WuzAPI>",
      "userID": "<id del user WuzAPI>",
      "event": {
        "Info": {
          "ID": "<msg uid>",
          "Sender": "<lid o jid>",            # puede ser @lid (no telefono)
          "SenderAlt": "<549...@s.whatsapp.net>",  # JID telefono real (preferir)
          "Chat": "<jid|@g.us>",
          "IsFromMe": false, "IsGroup": false,
          "PushName": "<nombre>",
          "Type": "text|image|...",
          "Timestamp": "<rfc3339>"
        },
        "Message": {
          "conversation": "<texto>",                       # texto simple
          "extendedTextMessage": {"text": "<texto>", "contextInfo": {...}},
          "imageMessage"/"documentMessage"/...: {...}       # media (TODO)
        }
      }
    }

Se normaliza al contrato común y se delega en whatsapp.account._process_inbound().
"""
import json
import logging
import mimetypes

from odoo import http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)

BASE = "/trixo_whatsapp/whatsmeow/webhook"

#: clave de mensaje de media -> (endpoint de descarga WuzAPI, tipo normalizado)
MEDIA_MESSAGES = {
    "imageMessage": ("/chat/downloadimage", "image"),
    "videoMessage": ("/chat/downloadvideo", "video"),
    "audioMessage": ("/chat/downloadaudio", "audio"),
    "documentMessage": ("/chat/downloaddocument", "document"),
    "stickerMessage": ("/chat/downloadimage", "sticker"),
}


class WhatsmeowWebhook(http.Controller):

    @http.route(BASE, methods=["POST"], type="http", auth="public", csrf=False)
    def receive(self):
        try:
            data = json.loads(request.httprequest.data or b"{}")
        except ValueError:
            return request.make_response("OK")

        if data.get("type") != "Message":
            # ReadReceipt / ChatPresence / etc.: pendiente (estados de entrega).
            return request.make_response("OK")

        event = data.get("event") or {}
        info = event.get("Info") or {}
        if info.get("IsFromMe"):
            return request.make_response("OK")  # no reprocesar salientes propios

        account = request.env["whatsapp.account"].sudo().search([
            ("provider", "=", "whatsmeow"),
            "|", ("whatsmeow_session_id", "=", data.get("userID")),
                 ("name", "=", data.get("instanceName")),
        ], limit=1)
        if not account:
            _logger.warning("WuzAPI webhook: cuenta no encontrada (userID=%s instance=%s)",
                            data.get("userID"), data.get("instanceName"))
            return request.make_response("OK")
        # TODO(hardening): verificar HMAC x-hmac-signature con la clave global de WuzAPI.

        # Remitente: preferir SenderAlt (telefono) sobre Sender (puede ser @lid).
        jid = info.get("SenderAlt") or info.get("Sender") or ""
        number = jid.split("@")[0].split(":")[0].split(".")[0]
        if not number:
            return request.make_response("OK")

        message = event.get("Message") or {}
        body = message.get("conversation")
        if not body:
            body = (message.get("extendedTextMessage") or {}).get("text")
        ctx = (message.get("extendedTextMessage") or {}).get("contextInfo") or {}

        norm = {
            "msg_uid": info.get("ID"),
            "from": number,
            "sender_name": info.get("PushName"),
            "type": "text",
            "body": plaintext2html(body) if body else None,
            "attachment": None,
            "reply_to_uid": ctx.get("stanzaId") or ctx.get("stanzaID"),
            "reaction": None,
            "raw": data,
        }

        # --- Media: el webhook trae solo la referencia cifrada; se descarga vía WuzAPI ---
        media_key = next((k for k in MEDIA_MESSAGES if k in message), None)
        if media_key:
            m = message[media_key] or {}
            endpoint, kind = MEDIA_MESSAGES[media_key]
            content = b""
            try:
                content = account._get_transport().download_inbound_media(endpoint, {
                    "Url": m.get("URL"),
                    "Mimetype": m.get("mimetype"),
                    "FileSHA256": m.get("fileSHA256"),
                    "FileLength": m.get("fileLength"),
                    "MediaKey": m.get("mediaKey"),
                    "FileEncSHA256": m.get("fileEncSHA256"),
                })
            except Exception:  # noqa: BLE001
                _logger.exception("WuzAPI webhook: fallo descargando media (%s)", kind)
            if content:
                fname = m.get("fileName")
                if not fname:
                    ext = mimetypes.guess_extension(m.get("mimetype") or "") or ""
                    fname = kind + ext
                norm["attachment"] = (fname, content, m.get("mimetype"))
                norm["type"] = kind
                caption = m.get("caption")
                norm["body"] = plaintext2html(caption) if caption else None

        if not norm["body"] and not norm["attachment"]:
            _logger.info("WuzAPI webhook: sin contenido manejable (type=%s, mediaType=%s)",
                         info.get("Type"), info.get("MediaType"))
            return request.make_response("OK")

        try:
            account._process_inbound(norm)
        except Exception:  # noqa: BLE001 - no devolver 500 al sidecar
            _logger.exception("WuzAPI webhook: error procesando entrante")
        return request.make_response("OK")
