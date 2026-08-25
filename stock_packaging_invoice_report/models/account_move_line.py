# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_round


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    packaging_quantity_invoice = fields.Float(
        string='Cantidad de Embalaje',
        compute='_compute_packaging_quantity_invoice',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes (bultos) equivalente a la cantidad de la '
             'linea, segun la unidad de embalaje por defecto del producto.',
        store=True,
    )

    packaging_name = fields.Char(
        string='Nombre del Embalaje',
        compute='_compute_packaging_name',
        help='Nombre del tipo de embalaje configurado en el sistema.',
        store=False,
    )

    @api.depends('quantity', 'product_id', 'product_uom_id')
    def _compute_packaging_quantity_invoice(self):
        """Odoo 19: el embalaje es una uom.uom del producto. La cantidad de
        bultos es la cantidad de la linea convertida a esa unidad (si la
        linea ya esta en bultos, es la cantidad tal cual)."""
        for line in self:
            line.packaging_quantity_invoice = 0.0
            if not line.product_id or not line.quantity or line.quantity <= 0:
                continue
            bulto = line.product_id._trixo_default_packaging_uom()
            if not bulto or not bulto.factor:
                continue
            src_uom = line.product_uom_id or line.product_id.uom_id
            line.packaging_quantity_invoice = float_round(
                src_uom._compute_quantity(line.quantity, bulto,
                                          rounding_method='HALF-UP'),
                precision_rounding=0.01,
            )

    def _compute_packaging_name(self):
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name', default='')
        for line in self:
            line.packaging_name = packaging_name
