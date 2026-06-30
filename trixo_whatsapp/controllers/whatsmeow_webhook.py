# Part of Trixocom.
"""Webhook entrante del sidecar WuzAPI.

NOTA (increment): el parser definitivo se escribe a partir del payload REAL de
WuzAPI (evento whatsmeow crudo: event.Info + event.Message). Mientras tanto este
controller registra el cuerpo crudo en el log para capturarlo, y responde 200 para
que WuzAPI no reintente.
"""
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

BASE = "/trixo_whatsapp/whatsmeow/webhook"


class WhatsmeowWebhook(http.Controller):

    @http.route(BASE, methods=["POST"], type="http", auth="public", csrf=False)
    def receive(self):
        raw = request.httprequest.data or b""
        ctype = request.httprequest.headers.get("Content-Type", "")
        _logger.warning("WUZAPI_WEBHOOK_RAW ctype=%s body=%s", ctype, raw[:4000])
        return request.make_response("OK")
