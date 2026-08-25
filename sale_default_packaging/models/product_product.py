# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _trixo_default_packaging_uom(self):
        """UoM de embalaje por defecto del producto: la primera de uom_ids
        cuyo nombre empiece con el nombre configurado (parametro
        stock_packaging_report.packaging_name, ej "Bulto" -> "Bulto x N").

        Helper compartido: lo usan sale_default_packaging (lineas de venta)
        y trixo_internal_transfer_pkg (movimientos de stock)."""
        self.ensure_one()
        name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name', default='')
        if not name:
            return self.env['uom.uom']
        return self.uom_ids.filtered(
            lambda u: u.name and u.name.lower().startswith(name.lower())
        )[:1]
