# Derivado de odoo/odoo master addons/pos_mercado_pago (LGPL-3), adaptado a Odoo 19 por Trixocom.
import hashlib
import hmac
import logging
import re

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosMercadoPagoWebhook(http.Controller):
    @http.route('/pos_mercado_pago/notification', methods=['POST'], type="http", auth="public", csrf=False)
    def notification(self, **kwargs):
        """ Procesa la notificación (webhook) de Mercado Pago, evento "Order".

        El formato es siempre JSON.
        """
        # Headers obligatorios
        x_request_id = request.httprequest.headers.get('X-Request-Id')
        if not x_request_id:
            _logger.warning('POST message received with no X-Request-Id in header')
            return http.Response(status=400)

        x_signature = request.httprequest.headers.get('X-Signature')
        if not x_signature:
            _logger.warning('POST message received with no X-Signature in header')
            return http.Response(status=400)

        ts_m = re.search(r"ts=(\d+)", x_signature)
        v1_m = re.search(r"v1=([a-f0-9]+)", x_signature)
        ts = ts_m.group(1) if ts_m else None
        v1 = v1_m.group(1) if v1_m else None
        if not ts or not v1:
            _logger.warning('Webhook bad X-Signature, ts: %s, v1: %s', ts, v1)
            return http.Response(status=400)

        # Payload
        data = request.httprequest.get_json(silent=True)
        if not data or data.get('type') != 'order':
            _logger.warning('POST message received with no or malformed data')
            return http.Response(status=400)

        # Si y solo si el webhook corresponde a una order creada por el POS
        # (ver payment_mercado_pago.js), data['data']['external_reference'] es
        # `XXX_YYY_ZZZ` donde XXX = session_id, YYY = payment_method_id y
        # ZZZ = uuid del pedido POS.
        external_reference = data.get('data', {}).get('external_reference')

        mercado_pago_pattern = r'(\d+)_(\d+)_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'

        if not external_reference or not (match := re.fullmatch(mercado_pago_pattern, external_reference)):
            _logger.warning('POST message received with no or malformed "external_reference" key: %s', external_reference)
            return http.Response(status=400)

        session_id, payment_method_id, _ = match.groups()

        pos_session_sudo = request.env['pos.session'].sudo().browse(int(session_id))
        if not pos_session_sudo.exists() or pos_session_sudo.state == 'closed':
            _logger.error("Invalid session id: %s", session_id)
            # No es un error de Mercado Pago: se acusa recibo igual
            return http.Response('OK', status=200)

        payment_method_sudo = pos_session_sudo.config_id.payment_method_ids.filtered(lambda p: p.id == int(payment_method_id))
        if not payment_method_sudo or payment_method_sudo.use_payment_terminal != 'mercado_pago':
            _logger.error("Invalid payment method id: %s", payment_method_id)
            return http.Response('OK', status=200)

        # Verificación de firma con la clave secreta. Mercado Pago firma con el
        # query param `data.id` en minúsculas aunque lo mande en mayúsculas.
        secret_key = payment_method_sudo.mp_webhook_secret_key or ''
        data_id = kwargs.get('data.id', '')
        signed_template = f"id:{data_id.lower()};request-id:{x_request_id};ts:{ts};"
        cyphed_signature = hmac.new(secret_key.encode(), signed_template.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(cyphed_signature, v1):
            _logger.error('Webhook authenticating failure, ts: %s, v1: %s', ts, v1)
            return http.Response(status=401)

        _logger.debug('Webhook authenticated, POST message: %s', data)

        # Avisar al POS (bus) que llegó un mensaje de Mercado Pago
        pos_session_sudo.config_id._notify('MERCADO_PAGO_LATEST_MESSAGE', {
            'payment_method_id': payment_method_sudo.id,
            'config_id': pos_session_sudo.config_id.id,
        })

        return http.Response('OK', status=200)
