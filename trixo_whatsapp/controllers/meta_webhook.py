# Part of Trixocom.
"""Webhook entrante de Meta Cloud API. Normaliza a evento común y delega en
whatsapp.account._process_inbound()."""
import hashlib
import hmac
import json
import logging
import mimetypes

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request
from odoo.tools import consteq, plaintext2html

_logger = logging.getLogger(__name__)

BASE = "/trixo_whatsapp/meta/webhook"


class MetaWebhook(http.Controller):

    @http.route(BASE, methods=["GET"], type="http", auth="public", csrf=False)
    def verify(self, **kw):
        token = kw.get("hub.verify_token")
        challenge = kw.get("hub.challenge")
        if kw.get("hub.mode") == "subscribe" and token:
            account = request.env["whatsapp.account"].sudo().search(
                [("meta_webhook_verify_token", "=", token)], limit=1)
            if account:
                return request.make_response(challenge)
        return Forbidden()

    @http.route(BASE, methods=["POST"], type="http", auth="public", csrf=False)
    def receive(self):
        raw = request.httprequest.data
        data = json.loads(raw or b"{}")
        for entry in data.get("entry", []):
            account = request.env["whatsapp.account"].sudo().search(
                [("meta_account_uid", "=", entry.get("id")),
                 ("provider", "=", "meta_cloud")], limit=1)
            if not account or not self._check_signature(account, raw):
                raise Forbidden()
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                value = change.get("value", {})
                # Estados de entrega (sent/delivered/read/failed) de mensajes salientes.
                if value.get("statuses"):
                    request.env["whatsapp.message"].sudo()._process_statuses(value)
                contacts = value.get("contacts", [{}])
                sender_name = contacts[0].get("profile", {}).get("name") if contacts else None
                for msg in value.get("messages", []):
                    event = self._normalize(account, msg, sender_name)
                    if event:
                        account._process_inbound(event)
        return request.make_response("OK")

    def _normalize(self, account, msg, sender_name):
        mtype = msg.get("type")
        event = {
            "msg_uid": msg.get("id"),
            "from": msg.get("from"),
            "sender_name": sender_name,
            "type": mtype,
            "body": None,
            "attachment": None,
            "reply_to_uid": (msg.get("context") or {}).get("id"),
            "reaction": None,
            "raw": msg,
        }
        if mtype == "text":
            event["body"] = plaintext2html(msg["text"]["body"])
        elif mtype in ("image", "document", "audio", "video", "sticker"):
            media = msg[mtype]
            content = account._get_transport().download_media(media["id"])
            filename = media.get("filename")
            if not filename:
                ext = mimetypes.guess_extension(media.get("mime_type") or "") or ""
                filename = mtype + ext
            event["attachment"] = (filename, content, media.get("mime_type"))
            if media.get("caption"):
                event["body"] = plaintext2html(media["caption"])
            event["type"] = "document" if mtype == "sticker" else mtype
        elif mtype == "reaction":
            event["type"] = "reaction"
            event["reaction"] = {
                "target_uid": msg["reaction"].get("message_id"),
                "emoji": msg["reaction"].get("emoji"),
            }
        else:
            _logger.info("Tipo de mensaje WhatsApp no soportado (Meta): %s", mtype)
            return None
        return event

    def _check_signature(self, account, raw):
        signature = request.httprequest.headers.get("X-Hub-Signature-256", "")
        secret = account.sudo().meta_app_secret
        if not signature.startswith("sha256=") or not secret:
            return False
        expected = hmac.new(secret.encode(), msg=raw,
                            digestmod=hashlib.sha256).hexdigest()
        return consteq(signature[7:], expected)
