# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_pos_created = fields.Boolean(string='Create from POS')

    @api.model
    def craete_saleorder_from_pos(self, oderdetails):
        vals = {}
        order_vals = {
            'partner_id': oderdetails.get('partner_id'),
            'date_order': datetime.date.today(),
            'is_pos_created': True,
            'state': 'draft',
            'amount_tax': oderdetails.get('tax_amount'),
        }
        if oderdetails.get('pricelist_id'):
            order_vals['pricelist_id'] = oderdetails.get('pricelist_id')
        saleorder_id = self.env['sale.order'].create(order_vals)
        vals['name'] = saleorder_id.name
        vals['id'] = saleorder_id.id
        for data in oderdetails:
            if data not in ('partner_id', 'tax_amount', 'pricelist_id'):
                current_dict = oderdetails.get(data)
                saleorder_id.order_line = [(0, 0, {
                    'product_id': current_dict.get('product'),
                    'product_uom_qty':  current_dict.get('quantity'),
                    'price_unit': current_dict.get('price'),
                    'discount': current_dict.get('discount'),
                })]
        return vals