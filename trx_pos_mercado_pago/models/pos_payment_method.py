# Derivado de odoo/odoo master addons/pos_mercado_pago (LGPL-3), adaptado a Odoo 19 por Trixocom.
import logging

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from .mercado_pago_pos_request import MERCADO_PAGO_PLATFORM_ID, MercadoPagoPosRequest

_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    mp_bearer_token = fields.Char(
        string="Production user token",
        help='Mercado Pago customer production user token: https://www.mercadopago.com.ar/developers/es/reference',
        groups="point_of_sale.group_pos_manager")
    mp_webhook_secret_key = fields.Char(
        string="Production secret key",
        help='Mercado Pago production secret key from integration application: https://www.mercadopago.com.ar/developers/panel/app',
        groups="point_of_sale.group_pos_manager")
    mp_id_point_smart = fields.Char(
        string="Terminal S/N",
        help="Enter your Point Smart terminal serial number written on the back of your terminal (after the S/N:)")
    mp_id_point_smart_complet = fields.Char()
    mp_webhook_endpoint = fields.Char(string="Mercado Pago Webhook Endpoint", compute='_compute_mp_webhook_endpoint', readonly=True)

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('mercado_pago', 'Mercado Pago')]

    def _check_special_access(self):
        if not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessError(_("Do not have access to fetch token from Mercado Pago"))

    def _compute_mp_webhook_endpoint(self):
        for record in self:
            web_base_url = record.get_base_url()
            record.mp_webhook_endpoint = f"{web_base_url}/pos_mercado_pago/notification"

    def force_pdv(self):
        """
        Botón (modo debug) para forzar el modo "PDV" del terminal vía
        PATCH /terminals/v1/setup. Cambia el modo del equipo físico.
        """
        self._check_special_access()

        mercado_pago = MercadoPagoPosRequest(self.sudo().mp_bearer_token)
        _logger.info('Calling Mercado Pago to force the terminal mode to "PDV"')

        payload = {"terminals": [{"id": self.mp_id_point_smart_complet, "operating_mode": "PDV"}]}
        resp = mercado_pago.call_mercado_pago("patch", "/terminals/v1/setup", payload)
        terminals = resp.get("terminals")
        if not terminals or terminals[0].get("operating_mode") != "PDV":
            raise UserError(_("Unexpected Mercado Pago response: %s", resp))
        _logger.debug("Successfully set the terminal mode to 'PDV'.")

    def mp_order_create(self, infos):
        """
        Llamado desde el POS para crear una order en Mercado Pago.
        """
        self._check_special_access()

        mercado_pago = MercadoPagoPosRequest(self.sudo().mp_bearer_token)
        infos['config'] = {
            'point': {
                'terminal_id': self.mp_id_point_smart_complet,
            },
        }
        infos['integration_data'] = {
            'platform_id': MERCADO_PAGO_PLATFORM_ID,
        }
        infos['expiration_time'] = 'PT30M'

        resp = mercado_pago.call_mercado_pago("post", "/v1/orders", infos, idempotent=True)
        _logger.debug("mp_order_create(), response from Mercado Pago: %s", resp)
        return resp

    def mp_order_get(self, order_id):
        """
        Llamado desde el POS para consultar el estado de una order.
        """
        self._check_special_access()

        mercado_pago = MercadoPagoPosRequest(self.sudo().mp_bearer_token)
        resp = mercado_pago.call_mercado_pago("get", f"/v1/orders/{order_id}", {})
        _logger.debug("mp_order_get(), response from Mercado Pago: %s", resp)
        return resp

    def mp_order_refund(self, order_id, amount=None):
        """
        Reembolso total (amount=None) o parcial de una order de Mercado Pago.
        """
        self._check_special_access()

        mercado_pago = MercadoPagoPosRequest(self.sudo().mp_bearer_token)
        if amount is None:
            body = {}
        else:
            order = self.mp_order_get(order_id)
            payments = order.get("transactions", {}).get("payments")
            if not payments:
                return {"errorMessage": _("Original Mercado Pago payment not found on order %s", order_id)}
            body = {"transactions": [{"id": payments[0]["id"], "amount": amount}]}
        resp = mercado_pago.call_mercado_pago("post", f"/v1/orders/{order_id}/refund", body, idempotent=True)
        _logger.debug("mp_order_refund(), response from Mercado Pago: %s", resp)
        return resp

    def _find_terminal(self, token, point_smart):
        mercado_pago = MercadoPagoPosRequest(token)
        data = mercado_pago.call_mercado_pago("get", "/terminals/v1/list", {}).get('data', {})
        if 'terminals' not in data:
            raise UserError(_("Please verify your production user token as it was rejected"))

        # Busca el terminal cuyo id contiene el S/N cargado por el usuario
        found_terminal = next((t for t in data['terminals'] if point_smart in t['id']), None)
        if not found_terminal:
            raise UserError(_("The terminal serial number is not registered on Mercado Pago"))
        return found_terminal.get('id', '')

    def write(self, vals):
        records = super().write(vals)

        if 'mp_id_point_smart' in vals or 'mp_bearer_token' in vals:
            for record in self.filtered(lambda r: r.use_payment_terminal == 'mercado_pago' and r.mp_bearer_token):
                record.mp_id_point_smart_complet = record._find_terminal(record.mp_bearer_token, record.mp_id_point_smart)

        return records

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            if record.use_payment_terminal == 'mercado_pago' and record.mp_bearer_token:
                record.mp_id_point_smart_complet = record._find_terminal(record.mp_bearer_token, record.mp_id_point_smart)

        return records
