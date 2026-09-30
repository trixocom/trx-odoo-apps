# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("order_id.fiscal_position_id")
    def _compute_tax_ids(self):
        """Recalcular los impuestos de las lineas cuando cambia la posicion
        fiscal del pedido (p.ej. al cambiar el tipo de pedido).

        El calculo nativo ya mapea los impuestos del producto con la posicion
        fiscal del pedido, pero solo se dispara al cambiar el producto o la
        compania: si la posicion fiscal cambia despues, las lineas cargadas
        conservan los impuestos viejos hasta que alguien aprieta "Actualizar
        impuestos". Aca solo se agrega la dependencia; el calculo es el nativo.
        """
        return super()._compute_tax_ids()
