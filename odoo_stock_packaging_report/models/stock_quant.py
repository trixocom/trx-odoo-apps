# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_round


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    packaging_quantity = fields.Float(
        string='Embalajes Disponibles',
        compute='_compute_packaging_quantity',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes disponibles calculada según el tipo de embalaje configurado en el sistema.'
    )

    @api.depends('available_quantity', 'product_id')
    def _compute_packaging_quantity(self):
        """
        Calcula la cantidad de embalajes disponibles basándose en:
        1. La cantidad disponible en el quant (available_quantity)
        2. El nombre del tipo de embalaje configurado en el sistema
        3. El qty definido en product.packaging para ese tipo de embalaje
        """
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        for quant in self:
            # Si no hay nombre de packaging configurado, mostrar qty en unidades
            if not packaging_name:
                quant.packaging_quantity = quant.available_quantity
                continue
            
            # Buscar el packaging con el nombre configurado para este producto
            packaging = self.env['product.packaging'].search([
                ('product_id', '=', quant.product_id.id),
                ('name', '=', packaging_name)
            ], limit=1)
            
            # Si no se encuentra el packaging o no tiene qty válido, mostrar qty en unidades
            if not packaging or packaging.qty <= 0:
                quant.packaging_quantity = quant.available_quantity
                continue
            
            # Calcular cantidad de embalajes: Stock / Unidades por Embalaje
            quant.packaging_quantity = float_round(
                quant.available_quantity / packaging.qty,
                precision_rounding=0.01
            )
