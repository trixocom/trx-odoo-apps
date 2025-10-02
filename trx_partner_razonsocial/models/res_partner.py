# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    razonsocial = fields.Char(
        string='Razón Social',
        help='Razón social o denominación legal del contacto'
    )
