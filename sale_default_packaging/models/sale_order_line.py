# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_packaging_uom_id = fields.Many2one(
        'uom.uom',
        string='Embalaje',
        help='Embalaje del producto (UoM)',
        check_company=True,
    )
    
    product_packaging_qty = fields.Float(
        string='Cantidad de Embalajes',
        default=1.0,
        digits='Product Unit of Measure',
        help='Cantidad de embalajes (se convertirá automáticamente a unidades de producto)'
    )

    @api.model
    def _get_default_packaging_name(self):
        """
        Obtiene el nombre del embalaje configurado en stock_packaging_report
        """
        config_param = self.env['ir.config_parameter'].sudo()
        packaging_name = config_param.get_param('stock_packaging_report.packaging_name', default='')
        return packaging_name

    @api.model
    def _get_default_packaging_uom(self):
        """
        Busca el packaging por defecto basándose en la configuración (UoM)
        """
        packaging_name = self._get_default_packaging_name()
        if not packaging_name:
            return False
            
        # Odoo 19: Search UoM by name
        packaging_uom = self.env['uom.uom'].search([
            ('name', '=', packaging_name)
        ], limit=1)
        
        return packaging_uom

    @api.onchange('product_id')
    def _onchange_product_id_set_default_packaging(self):
        """
        Establece el embalaje por defecto cuando se selecciona un producto
        """
        if self.product_id:
            packaging_uom = self._get_default_packaging_uom()
            
            if packaging_uom:
                self.product_packaging_uom_id = packaging_uom.id
                self.product_packaging_qty = 1.0
                # Calcular la cantidad de producto basada en el packaging
                if packaging_uom.factor_inv:
                    self.product_uom_qty = self.product_packaging_qty * packaging_uom.factor_inv
            else:
                # Si no hay packaging configurado, establecer valores por defecto
                self.product_packaging_uom_id = False
                self.product_packaging_qty = 1.0

    @api.onchange('product_packaging_qty', 'product_packaging_uom_id')
    def _onchange_packaging_qty_update_product_qty(self):
        """
        Actualiza la cantidad de producto basada en la cantidad de embalajes
        """
        if self.product_packaging_uom_id and self.product_packaging_qty:
            # Calcular la cantidad de unidades basada en embalajes
            # Cantidad de producto = Cantidad de embalajes * Unidades por embalaje
            if self.product_packaging_uom_id.factor_inv:
                self.product_uom_qty = self.product_packaging_qty * self.product_packaging_uom_id.factor_inv

    @api.onchange('product_uom_qty')
    def _onchange_product_qty_update_packaging_qty(self):
        """
        Actualiza la cantidad de embalajes cuando cambia la cantidad de producto
        """
        if self.product_packaging_uom_id and self.product_uom_qty and self.product_packaging_uom_id.factor_inv:
            # Calcular cuántos embalajes completos hay
            self.product_packaging_qty = self.product_uom_qty / self.product_packaging_uom_id.factor_inv

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para establecer valores por defecto al crear líneas
        """
        for vals in vals_list:
            if 'product_id' in vals and vals.get('product_id'):
                product_id = vals.get('product_id')
                
                # Si no se especifica packaging, buscar el por defecto
                if 'product_packaging_uom_id' not in vals:
                    packaging_uom = self._get_default_packaging_uom()
                    
                    if packaging_uom:
                        vals['product_packaging_uom_id'] = packaging_uom.id
                        
                        # Si no se especifica cantidad de packaging, usar 1
                        if 'product_packaging_qty' not in vals:
                            vals['product_packaging_qty'] = 1.0
                        
                        # Calcular cantidad de producto si no está especificada
                        if 'product_uom_qty' not in vals and packaging_uom.factor_inv:
                            vals['product_uom_qty'] = vals.get('product_packaging_qty', 1.0) * packaging_uom.factor_inv
        
        return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        """
        Override write para mantener sincronizadas las cantidades
        """
        # Si se cambia el packaging, recalcular las cantidades
        if 'product_packaging_uom_id' in vals:
            for line in self:
                # Odoo 19: browse UoM
                packaging_uom = self.env['uom.uom'].browse(vals['product_packaging_uom_id'])
                if packaging_uom and packaging_uom.factor_inv and line.product_packaging_qty:
                    vals['product_uom_qty'] = line.product_packaging_qty * packaging_uom.factor_inv
        
        return super(SaleOrderLine, self).write(vals)
