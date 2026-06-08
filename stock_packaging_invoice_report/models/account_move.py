# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    total_bultos = fields.Float(
        string='Total Bultos',
        compute='_compute_total_bultos',
        digits='Product Unit of Measure',
        help='Suma total de bultos de la factura.'
    )

    @api.depends('invoice_line_ids.packaging_quantity_invoice')
    def _compute_total_bultos(self):
        for move in self:
            move.total_bultos = sum(
                line.packaging_quantity_invoice
                for line in move.invoice_line_ids
                if line.display_type not in ('line_section', 'line_note')
            )
