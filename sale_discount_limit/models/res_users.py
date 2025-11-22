# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    max_discount = fields.Float(
        string='Descuento Máximo (%)',
        default=0.0,
        help='Descuento máximo permitido para este usuario en órdenes de venta. '
             'Si es 0, el usuario no podrá aplicar descuentos.'
    )
