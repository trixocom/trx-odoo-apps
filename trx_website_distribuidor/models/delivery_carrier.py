from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _is_available_for_order(self, order):
        res = super()._is_available_for_order(order)
        if res and self.delivery_type == "in_store":
            user = self.env.user
            # Retiro/pago en el local: solo distribuidores (y el backend).
            return user._is_internal() or user._trx_es_distribuidor()
        return res
