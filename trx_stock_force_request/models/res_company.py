# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    trx_block_negative_stock = fields.Boolean(
        string='Bloquear stock negativo',
        default=True,
        help='Al validar un movimiento que sale de una ubicacion interna se '
             'verifica que el stock no quede negativo. Solo se exceptua el '
             'despacho con una solicitud de forzado aprobada.',
    )
