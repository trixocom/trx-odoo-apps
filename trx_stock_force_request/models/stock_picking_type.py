# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    trx_force_approver_id = fields.Many2one(
        'res.users',
        string='Aprueba forzado de stock',
        domain=lambda self: [('all_group_ids', 'in',
                              self.env.ref('trx_stock_force_request.group_force_approver').id)],
        help='Usuario que recibe las solicitudes de forzado de stock de este '
             'tipo de operacion. Si queda vacio, se notifica a todos los '
             'usuarios del grupo "Aprobar forzado de stock".',
    )
