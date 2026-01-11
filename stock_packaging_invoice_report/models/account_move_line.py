# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_round


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    packaging_quantity_invoice = fields.Float(
        string='Cantidad de Embalaje',
        compute='_compute_packaging_quantity_invoice',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes calculada según el tipo de embalaje configurado en el sistema.',
        store=True
    )

    packaging_name = fields.Char(
        string='Nombre del Embalaje',
        compute='_compute_packaging_name',
        help='Nombre del tipo de embalaje configurado en el sistema.',
        store=False
    )

    @api.depends('quantity', 'product_id')
    def _compute_packaging_quantity_invoice(self):
        """
        Calcula la cantidad de embalajes para la línea de factura basándose en:
        1. La cantidad del producto en la línea de factura
        2. El nombre del tipo de embalaje configurado en el sistema
        3. El qty definido en product.packaging para ese tipo de embalaje
        """
        # Obtener el nombre del packaging configurado en el sistema
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        for line in self:
            line.packaging_quantity_invoice = 0.0
            
            # Solo procesar líneas con producto y cantidad válida
            if not line.product_id or not line.quantity or line.quantity <= 0:
                continue
            
            # Si no hay nombre de packaging configurado, no calcular
            if not packaging_name:
                continue
            
            # Odoo 19: Unification - Search UoM by name
            packaging_uom = self.env['uom.uom'].search([
                ('name', '=', packaging_name)
            ], limit=1)
            
            # Si no se encuentra el packaging o no tiene factor_inv válido, no calcular
            if not packaging_uom or packaging_uom.factor_inv <= 0:
                continue
            
            # Calcular cantidad de embalajes: Cantidad en línea / Unidades por Embalaje
            quantity = line.quantity
            packaging_qty = packaging_uom.factor_inv
            
            line.packaging_quantity_invoice = float_round(
                quantity / packaging_qty,
                precision_rounding=0.01
            )

    def _compute_packaging_name(self):
        """
        Obtiene el nombre del embalaje configurado en el sistema para mostrar en la vista.
        """
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name',
            default=''
        )
        
        for line in self:
            line.packaging_name = packaging_name