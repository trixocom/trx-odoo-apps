# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _apply_order_type_prices(self):
        """Recalcula precios y descuentos de las lineas segun la lista de
        precios vigente en la orden (equivalente al boton 'Actualizar
        precios'). Solo se aplica si el tipo de pedido define una lista de
        precios, ya que ese es el caso en que el tipo cambia la lista."""
        for order in self:
            if order.type_id.pricelist_id and order.order_line:
                order._recompute_prices()

    @api.onchange("type_id")
    def _onchange_type_id_update_prices(self):
        """En el formulario: al elegir un tipo de pedido que trae lista de
        precios propia, aplicar esa lista a las lineas existentes."""
        self._apply_order_type_prices()

    def write(self, vals):
        res = super().write(vals)
        if vals.get("type_id"):
            orders = self.filtered(
                lambda o: o.state in ("draft", "sent")
                and o.type_id.pricelist_id
                and o.order_line
            )
            orders._apply_order_type_prices()
        return res
