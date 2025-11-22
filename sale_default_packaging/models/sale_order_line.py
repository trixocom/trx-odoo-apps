# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_packaging_id = fields.Many2one(
        'product.packaging',
        string='Embalaje',
        help='Embalaje del producto',
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
    def _get_default_packaging_for_product(self, product_id):
        """
        Busca el packaging por defecto para un producto basándose en la configuración
        """
        if not product_id:
            return False
            
        packaging_name = self._get_default_packaging_name()
        if not packaging_name:
            return False
            
        # Buscar el packaging del producto que coincida con el nombre configurado
        packaging = self.env['product.packaging'].search([
            ('product_id', '=', product_id),
            ('name', '=', packaging_name)
        ], limit=1)
        
        return packaging

    @api.onchange('product_id')
    def _onchange_product_id_set_default_packaging(self):
        """
        Establece el embalaje por defecto cuando se selecciona un producto
        """
        if self.product_id:
            packaging = self._get_default_packaging_for_product(self.product_id.id)
            
            if packaging:
                self.product_packaging_id = packaging.id
                self.product_packaging_qty = 1.0
                # Calcular la cantidad de producto basada en el packaging
                if packaging.qty:
                    self.product_uom_qty = self.product_packaging_qty * packaging.qty
            else:
                # Si no hay packaging configurado, establecer valores por defecto
                self.product_packaging_id = False
                self.product_packaging_qty = 1.0

    @api.onchange('product_packaging_qty', 'product_packaging_id')
    def _onchange_packaging_qty_update_product_qty(self):
        """
        Actualiza la cantidad de producto basada en la cantidad de embalajes
        """
        if self.product_packaging_id and self.product_packaging_qty:
            # Calcular la cantidad de unidades basada en embalajes
            # Cantidad de producto = Cantidad de embalajes * Unidades por embalaje
            if self.product_packaging_id.qty:
                self.product_uom_qty = self.product_packaging_qty * self.product_packaging_id.qty

    @api.onchange('product_uom_qty')
    def _onchange_product_qty_update_packaging_qty(self):
        """
        Actualiza la cantidad de embalajes cuando cambia la cantidad de producto
        """
        if self.product_packaging_id and self.product_uom_qty and self.product_packaging_id.qty:
            # Calcular cuántos embalajes completos hay
            self.product_packaging_qty = self.product_uom_qty / self.product_packaging_id.qty

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create para establecer valores por defecto al crear líneas
        """
        for vals in vals_list:
            if 'product_id' in vals and vals.get('product_id'):
                product_id = vals.get('product_id')
                
                # Si no se especifica packaging, buscar el por defecto
                if 'product_packaging_id' not in vals:
                    packaging = self._get_default_packaging_for_product(product_id)
                    
                    if packaging:
                        vals['product_packaging_id'] = packaging.id
                        
                        # Si no se especifica cantidad de packaging, usar 1
                        if 'product_packaging_qty' not in vals:
                            vals['product_packaging_qty'] = 1.0
                        
                        # Calcular cantidad de producto si no está especificada
                        if 'product_uom_qty' not in vals and packaging.qty:
                            vals['product_uom_qty'] = vals.get('product_packaging_qty', 1.0) * packaging.qty
        
        return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        """
        Override write para mantener sincronizadas las cantidades
        """
        # Si se cambia el packaging, recalcular las cantidades
        if 'product_packaging_id' in vals:
            for line in self:
                packaging = self.env['product.packaging'].browse(vals['product_packaging_id'])
                if packaging and packaging.qty and line.product_packaging_qty:
                    vals['product_uom_qty'] = line.product_packaging_qty * packaging.qty
        
        return super(SaleOrderLine, self).write(vals)
