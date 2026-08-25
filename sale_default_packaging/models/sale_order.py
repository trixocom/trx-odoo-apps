# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_bultos = fields.Float(
        string='Total Bultos',
        compute='_compute_total_bultos',
        digits='Product Unit of Measure',
        help='Suma total de bultos del pedido. Incluye lineas en UoM de '
             'embalaje y lineas en unidades con embalaje default del '
             'producto (derivadas por factor — pedidos migrados de v18).',
    )

    @api.depends('order_line.trixo_pkg_qty')
    def _compute_total_bultos(self):
        for order in self:
            order.total_bultos = sum(order.order_line.mapped('trixo_pkg_qty'))
