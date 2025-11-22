# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        readonly=True,
        copy=False,
        help="Orden de venta creada desde el POS"
    )

    def create_sale_order_from_pos(self):
        """
        Crea una orden de venta desde la orden del POS
        Basado en la funcionalidad de wt_create_so_from_pos
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_('Debe seleccionar un cliente para crear la orden de venta.'))
        
        if self.sale_order_id:
            raise UserError(_('Esta orden de POS ya tiene una orden de venta asociada: %s') % self.sale_order_id.name)

        # Preparar valores para la orden de venta
        sale_order_vals = self._prepare_sale_order_values()
        
        # Crear la orden de venta
        sale_order = self.env['sale.order'].create(sale_order_vals)
        
        # Crear las líneas de la orden de venta
        for line in self.lines:
            if line.qty > 0:  # Solo líneas con cantidad positiva
                sale_line_vals = self._prepare_sale_order_line_values(line, sale_order)
                self.env['sale.order.line'].create(sale_line_vals)
        
        # Vincular la orden de venta con la orden del POS
        self.sale_order_id = sale_order.id
        
        # Marcar la orden del POS como procesada
        self.state = 'done'
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Orden de Venta'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _prepare_sale_order_values(self):
        """
        Prepara los valores para crear la orden de venta
        """
        self.ensure_one()
        
        # Obtener el equipo de ventas predeterminado o el del usuario
        team = self.env['crm.team']._get_default_team_id()
        
        # Obtener la lista de precios
        pricelist = self.pricelist_id or self.partner_id.property_product_pricelist
        
        return {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'pricelist_id': pricelist.id,
            'date_order': self.date_order,
            'user_id': self.user_id.id,
            'team_id': team.id if team else False,
            'company_id': self.company_id.id,
            'note': self.note or '',
            'origin': _('POS Order: %s') % self.name,
        }

    def _prepare_sale_order_line_values(self, pos_line, sale_order):
        """
        Prepara los valores para crear una línea de orden de venta
        """
        # Obtener el precio unitario sin impuestos
        price_unit = pos_line.price_unit
        
        # Calcular el descuento si existe
        discount = pos_line.discount
        
        return {
            'order_id': sale_order.id,
            'product_id': pos_line.product_id.id,
            'product_uom_qty': pos_line.qty,
            'product_uom': pos_line.product_id.uom_id.id,
            'price_unit': price_unit,
            'discount': discount,
            'tax_id': [(6, 0, pos_line.tax_ids_after_fiscal_position.ids)],
            'name': pos_line.full_product_name,
        }

    @api.model
    def create_from_ui(self, orders, draft=False):
        """
        Override para manejar la creación de órdenes desde la UI del POS
        """
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        
        # Procesar las órdenes que tienen el flag create_sale_order
        for order_data in orders:
            if order_data.get('data', {}).get('create_sale_order'):
                # Buscar la orden creada
                pos_reference = order_data.get('data', {}).get('name')
                if pos_reference:
                    pos_order = self.search([('pos_reference', '=', pos_reference)], limit=1)
                    if pos_order and not pos_order.sale_order_id:
                        try:
                            pos_order.create_sale_order_from_pos()
                        except Exception as e:
                            # Log del error pero no fallar toda la operación
                            _logger.error(f"Error creating sale order from POS: {e}")
        
        return order_ids

    @api.model
    def create_sale_order_from_ui(self, order_data):
        """
        Método llamado desde el frontend para crear la orden de venta
        """
        # Crear la orden del POS primero
        order_list = [{'data': order_data}]
        order_ids = self.create_from_ui(order_list, draft=False)
        
        if order_ids and len(order_ids) > 0:
            order_id = order_ids[0].get('id')
            pos_order = self.browse(order_id)
            
            # Crear la orden de venta
            result = pos_order.create_sale_order_from_pos()
            
            if isinstance(result, dict) and result.get('type') == 'ir.actions.act_window':
                return {
                    'success': True,
                    'sale_order_id': pos_order.sale_order_id.id,
                    'sale_order_name': pos_order.sale_order_id.name,
                    'pos_order_id': pos_order.id,
                }
        
        return {
            'success': False,
            'error': _('Error al procesar la orden'),
        }


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @property
    def full_product_name(self):
        """
        Retorna el nombre completo del producto incluyendo variantes
        """
        variant = self.product_id.product_template_attribute_value_ids._get_combination_name()
        if variant:
            return f"{self.product_id.name} ({variant})"
        return self.product_id.name
