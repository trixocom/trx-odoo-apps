# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_bultos = fields.Float(
        string='Total Bultos',
        compute='_compute_total_bultos',
        digits='Product Unit of Measure',
        help='Suma total de bultos del pedido de venta basados en UoM.'
    )

    @api.depends('order_line.product_packaging_qty', 'order_line.product_packaging_uom_id')
    def _compute_total_bultos(self):
        for order in self:
            order.total_bultos = sum(
                line.product_packaging_qty
                for line in order.order_line
                if line.product_packaging_uom_id
            )
