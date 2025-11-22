# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_round


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    packaging_quantity_available = fields.Float(
        string='Embalajes Disponibles',
        compute='_compute_packaging_quantity_available',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes disponibles calculada según el tipo de embalaje configurado en el sistema.'
    )
    
    packaging_virtual_available = fields.Float(
        string='Embalajes Pronosticados',
        compute='_compute_packaging_virtual_available',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes pronosticados calculada según el tipo de embalaje configurado en el sistema.'
    )
    
    packaging_name_display = fields.Char(
        string='Nombre del Embalaje',
        compute='_compute_packaging_name_display',
        help='Nombre del tipo de embalaje configurado para mostrar en el smart button'
    )

    def _calculate_packaging_qty(self, unit_qty):
        """
        Método auxiliar para calcular cantidad de embalajes desde unidades
        """
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        # Si no hay nombre de packaging configurado, retornar qty en unidades
        if not packaging_name:
            return unit_qty
        
        # Si es variante única, calcular según el packaging
        if len(self.product_variant_ids) == 1:
            variant = self.product_variant_ids[0]
            # Buscar el packaging con el nombre configurado para esta variante
            packaging = self.env['product.packaging'].search([
                ('product_id', '=', variant.id),
                ('name', '=', packaging_name)
            ], limit=1)
            
            # Si no se encuentra el packaging o no tiene qty válido, retornar qty en unidades
            if not packaging or packaging.qty <= 0:
                return unit_qty
            
            # Calcular cantidad de embalajes: Stock / Unidades por Embalaje
            return float_round(
                unit_qty / packaging.qty,
                precision_rounding=0.01
            )
        else:
            # Si tiene múltiples variantes, retornar en unidades
            return unit_qty

    @api.depends('qty_available')
    def _compute_packaging_quantity_available(self):
        """
        Calcula la cantidad de embalajes disponibles basándose en:
        1. La cantidad disponible del producto (qty_available)
        2. El nombre del tipo de embalaje configurado en el sistema
        3. El qty definido en product.packaging para ese tipo de embalaje
        """
        for template in self:
            template.packaging_quantity_available = template._calculate_packaging_qty(
                template.qty_available
            )

    @api.depends('virtual_available')
    def _compute_packaging_virtual_available(self):
        """
        Calcula la cantidad de embalajes pronosticados basándose en:
        1. La cantidad pronosticada del producto (virtual_available)
        2. El nombre del tipo de embalaje configurado en el sistema
        3. El qty definido en product.packaging para ese tipo de embalaje
        """
        for template in self:
            template.packaging_virtual_available = template._calculate_packaging_qty(
                template.virtual_available
            )

    @api.depends('product_variant_ids')
    def _compute_packaging_name_display(self):
        """
        Obtiene el nombre del embalaje configurado para mostrarlo en el smart button
        """
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        for template in self:
            if packaging_name:
                template.packaging_name_display = packaging_name
            else:
                template.packaging_name_display = 'U'
