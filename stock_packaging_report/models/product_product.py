# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License LGPL-3.0 or later
from odoo import api, fields, models
from odoo.tools.float_utils import float_round

# Contextos que ya traen una ubicacion/almacen explicito: si el usuario o el
# codigo llamador pidieron un almacen concreto, no lo pisamos con el del usuario.
_EXPLICIT_LOCATION_KEYS = ('warehouse_id', 'search_warehouse', 'warehouse', 'location')


class ProductProduct(models.Model):
    _inherit = 'product.product'

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

    # ------------------------------------------------------------------
    # Almacen por defecto del usuario
    # ------------------------------------------------------------------
    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        """Filtra las cantidades por el almacen por defecto del usuario.

        Solo se inyecta si nadie pidio ya un almacen o ubicacion concreta. La
        clave de contexto es 'warehouse_id', que es la que lee
        stock.product._get_domain_locations() en Odoo 19.
        """
        warehouse = self.env.user.property_warehouse_id
        if warehouse and not any(self.env.context.get(k) for k in _EXPLICIT_LOCATION_KEYS):
            self = self.with_context(warehouse_id=warehouse.id)
        return super(ProductProduct, self)._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date, to_date)

    # ------------------------------------------------------------------
    # Conversion a bultos
    # ------------------------------------------------------------------
    def _packaging_convert(self, qty, packaging_uom):
        """Convierte qty (en la UoM de referencia del producto) a bultos."""
        self.ensure_one()
        if not packaging_uom or not qty:
            return 0.0
        converted = self.uom_id._compute_quantity(
            qty, packaging_uom, round=False, raise_if_failure=False)
        return float_round(converted, precision_rounding=0.01)

    @api.depends('qty_available', 'virtual_available', 'uom_ids', 'uom_id')
    def _compute_packaging_quantities(self):
        packaging_name = self.env['ir.config_parameter'].sudo().get_param(
            'stock_packaging_report.packaging_name', default='')
        for product in self:
            packaging_uom = product._trixo_default_packaging_uom() if packaging_name else False
            product.packaging_name_display = packaging_name if packaging_uom else ''
            product.packaging_quantity_available = product._packaging_convert(
                product.qty_available, packaging_uom)
            product.packaging_virtual_available = product._packaging_convert(
                product.virtual_available, packaging_uom)

    # ------------------------------------------------------------------
    # Busqueda
    # ------------------------------------------------------------------
    def _search_packaging_quantity_available(self, operator, value):
        return self._search_packaging_field('packaging_quantity_available', operator, value)

    def _search_packaging_virtual_available(self, operator, value):
        return self._search_packaging_field('packaging_virtual_available', operator, value)

    @api.model
    def _search_packaging_field(self, fname, operator, value):
        """Busqueda sobre un campo calculado no almacenado.

        No hay forma de resolverlo en SQL porque el divisor (unidades por
        bulto) es distinto por producto. Acotamos el barrido a los productos
        almacenables activos y dejamos que el ORM calcule en lote.
        """
        if operator not in ('=', '!=', '<', '<=', '>', '>='):
            return NotImplemented
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return NotImplemented
        candidates = self.with_context(active_test=True).search([('is_storable', '=', True)])
        # Fuerza el calculo en lote de una sola pasada.
        candidates.mapped(fname)
        checks = {
            '=': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
        }
        check = checks[operator]
        return [('id', 'in', [p.id for p in candidates if check(p[fname], value)])]
