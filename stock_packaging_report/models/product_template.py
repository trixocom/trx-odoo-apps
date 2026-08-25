# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License LGPL-3.0 or later
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    packaging_quantity_available = fields.Float(
        string='Embalajes Disponibles',
        compute='_compute_packaging_quantities',
        search='_search_packaging_quantity_available',
        digits='Product Unit of Measure',
        help='Cantidad a mano expresada en la unidad de embalaje configurada '
             'en Inventario > Configuracion > Ajustes.',
    )

    packaging_virtual_available = fields.Float(
        string='Embalajes Pronosticados',
        compute='_compute_packaging_quantities',
        search='_search_packaging_virtual_available',
        digits='Product Unit of Measure',
        help='Cantidad pronosticada expresada en la unidad de embalaje '
             'configurada en Inventario > Configuracion > Ajustes.',
    )

    packaging_name_display = fields.Char(
        string='Unidad de Embalaje',
        compute='_compute_packaging_quantities',
        help='Nombre del embalaje configurado. Vacio si el producto no tiene '
             'esa unidad de embalaje definida.',
    )

    @api.depends('product_variant_ids.packaging_quantity_available',
                 'product_variant_ids.packaging_virtual_available',
                 'product_variant_ids.packaging_name_display')
    def _compute_packaging_quantities(self):
        """Solo tiene sentido con una unica variante: con varias, cada una
        puede tener un bulto distinto y sumarlas seria enganoso."""
        for template in self:
            variants = template.product_variant_ids
            if len(variants) == 1:
                template.packaging_quantity_available = variants.packaging_quantity_available
                template.packaging_virtual_available = variants.packaging_virtual_available
                template.packaging_name_display = variants.packaging_name_display
            else:
                template.packaging_quantity_available = 0.0
                template.packaging_virtual_available = 0.0
                template.packaging_name_display = ''

    def _search_packaging_quantity_available(self, operator, value):
        return self._search_packaging_field('packaging_quantity_available', operator, value)

    def _search_packaging_virtual_available(self, operator, value):
        return self._search_packaging_field('packaging_virtual_available', operator, value)

    @api.model
    def _search_packaging_field(self, fname, operator, value):
        variant_domain = self.env['product.product']._search_packaging_field(
            fname, operator, value)
        if variant_domain is NotImplemented:
            return NotImplemented
        variants = self.env['product.product'].search(variant_domain)
        return [('id', 'in', variants.product_tmpl_id.ids)]
