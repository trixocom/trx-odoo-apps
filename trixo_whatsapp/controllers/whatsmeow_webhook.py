# Part of Trixocom.
"""Webhook entrante del sidecar whatsmeow. El sidecar empuja eventos ya cercanos
al contrato común; aquí terminamos de normalizar y delegamos en _process_inbound().

Payload esperado del sidecar (contrato Trixocom)::

    {
      "session_id": "<id>",
      "type": "text|image|document|audio|video|location|reaction",
      "msg_uid": "<id>",
      "from": "<e164 sin +>",
      "sender_name": "<str>",
      "body": "<texto o caption>",
      "reply_to_uid": "<id|null>",
      "media_ref": "<ref para descargar|null>",
      "filename": "<str|null>",
      "mimetype": "<str|null>",
      "reaction": {"target_uid": "<id>", "emoji": "<str>"}
    }
"""
import json
import logging
import mimetypes

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.http import request
from odoo.tools import consteq, plaintext2html

_logger = logging.getLogger(__name__)

BASE = "/trixo_whatsapp/whatsmeow/webhook"


class WhatsmeowWebhook(http.Controller):

    @http.route(BASE, methods=["POST"], type="http", auth="public", csrf=False)
    def receive(self):
        data = json.loads(request.httprequest.data or b"{}")
        account = request.env["whatsapp.account"].sudo().search(
            [("whatsmeow_session_id", "=", data.get("session_id")),
             ("provider", "=", "whatsmeow")], limit=1)
        if not account or not self._check_token(account):
            raise Forbidden()

        mtype = data.get("type")
        event = {
            "msg_uid": data.get("msg_uid"),
            "from": data.get("from"),
            "sender_name": data.get("sender_name"),
            "type": mtype,
            "body": plaintext2html(data["body"]) if data.get("body") else None,
            "attachment": None,
            "reply_to_uid": data.get("reply_to_uid"),
            "reaction": data.get("reaction"),
            "raw": data,
        }
        if data.get("media_ref"):
            content = account._get_transport().download_media(data["media_ref"])
            filename = data.get("filename")
            if not filename:
                ext = mimetypes.guess_extension(data.get("mimetype") or "") or ""
                filename = (mtype or "file") + ext
            event["attachment"] = (filename, content, data.get("mimetype"))
        account._process_inbound(event)
        return request.make_response("OK")

    def _check_token(self, account):
        token = account.sudo().whatsmeow_token
        if not token:
            return True  # sin token configurado: red interna confiable
        sent = request.httprequest.headers.get("Authorization", "")
        return sent.startswith("Bearer ") and consteq(sent[7:], token)
