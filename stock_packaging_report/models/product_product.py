# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    packaging_quantity_available = fields.Float(
        string='Embalajes Disponibles',
        compute='_compute_packaging_quantity_available',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes disponibles calculada según el tipo de embalaje configurado en el sistema.'
    )

    @api.depends('qty_available')
    def _compute_packaging_quantity_available(self):
        """
        Calcula la cantidad de embalajes disponibles basándose en:
        1. La cantidad disponible del producto (qty_available)
        2. El nombre del tipo de embalaje configurado en el sistema
        3. El qty definido en product.packaging para ese tipo de embalaje
        """
        # Obtener el nombre del packaging configurado en el sistema
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        for product in self:
            product.packaging_quantity_available = 0.0
            
            # Si no hay nombre de packaging configurado, no calcular
            if not packaging_name:
                continue
            
            # Buscar el packaging con el nombre configurado para este producto
            packaging = self.env['product.packaging'].search([
                ('product_id', '=', product.id),
                ('name', '=', packaging_name)
            ], limit=1)
            
            # Si no se encuentra el packaging o no tiene qty válido, no calcular
            if not packaging or packaging.qty <= 0:
                continue
            
            # Calcular cantidad de embalajes: Stock Disponible / Unidades por Embalaje
            qty_available = product.qty_available
            packaging_qty = packaging.qty
            
            product.packaging_quantity_available = float_round(
                qty_available / packaging_qty,
                precision_rounding=0.01
            )
