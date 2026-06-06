# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_show_update_prices(self):
        """Los precios y descuentos de las lineas se actualizan solos (via
        compute dependiente de pricelist_id) cuando cambia la lista de precios
        de la orden, p.ej. al cambiar el tipo de pedido. Por eso no mostramos
        el aviso 'Actualizar precios': el ajuste es automatico."""
        self.show_update_pricelist = False
