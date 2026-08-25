# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    trixo_units_qty = fields.Float(
        string='Unidades',
        compute='_compute_trixo_units_qty',
        digits='Product Unit of Measure',
        help='Cantidad de la linea convertida a la unidad base del producto. '
             'Si la linea esta en Bultos, muestra el total de unidades.',
    )
    # v19.0.2.2.0: columnas Embalaje / Cant Emb. con derivacion para lineas
    # en unidades (pedidos migrados de v18, donde la cantidad quedo en la
    # UoM base): si la linea no esta en la UoM de embalaje pero el producto
    # tiene embalaje default, se convierte la cantidad al embalaje.
    trixo_pkg_uom_name = fields.Char(
        string='Embalaje',
        compute='_compute_trixo_pkg',
    )
    trixo_pkg_qty = fields.Float(
        string='Cant Emb.',
        compute='_compute_trixo_pkg',
        digits='Product Unit of Measure',
    )

    @api.model
    def _get_default_packaging_name(self):
        """Nombre del embalaje por defecto (parametro
        stock_packaging_report.packaging_name, ej: "Bulto"). Se conserva la
        clave del 18 por continuidad con los datos migrados."""
        config_param = self.env['ir.config_parameter'].sudo()
        return config_param.get_param(
            'stock_packaging_report.packaging_name', default='')

    def _get_default_packaging_uom(self, product):
        """Delegado al helper compartido de product.product (lo usa tambien
        trixo_internal_transfer_pkg para movimientos de stock)."""
        if not product:
            return self.env['uom.uom']
        return product._trixo_default_packaging_uom()

    def _compute_product_uom_id(self):
        """Al elegir producto: si tiene embalaje por defecto, la linea queda
        en esa UoM (1 Bulto por el default de cantidad), igual que en 18.
        En Odoo 19 product_uom_id es un campo computado (store,
        readonly=False): un @api.onchange seria pisado por el compute nativo,
        asi que el default se engancha aca. El usuario puede cambiar la UoM
        a mano despues (el compute solo re-corre al cambiar el producto)."""
        super()._compute_product_uom_id()
        for line in self:
            if line.product_id:
                uom = self._get_default_packaging_uom(line.product_id)
                if uom:
                    line.product_uom_id = uom

    @api.depends('product_uom_qty', 'product_uom_id', 'product_id')
    def _compute_trixo_units_qty(self):
        for line in self:
            if line.product_id and line.product_uom_id:
                line.trixo_units_qty = line.product_uom_id._compute_quantity(
                    line.product_uom_qty, line.product_id.uom_id)
            else:
                line.trixo_units_qty = line.product_uom_qty

    @api.depends('product_uom_qty', 'product_uom_id', 'product_id')
    def _compute_trixo_pkg(self):
        for line in self:
            pkg_name = ''
            pkg_qty = 0.0
            prod = line.product_id
            uom = line.product_uom_id
            if prod and uom:
                if uom != prod.uom_id and uom in prod.uom_ids:
                    # La linea YA esta en un embalaje del producto.
                    pkg_name = uom.name
                    pkg_qty = line.product_uom_qty
                else:
                    # Linea en unidades (tipico de pedidos migrados de 18):
                    # derivar bultos con el embalaje default del producto.
                    pkg_uom = prod._trixo_default_packaging_uom()
                    if pkg_uom:
                        pkg_name = pkg_uom.name
                        pkg_qty = uom._compute_quantity(
                            line.product_uom_qty, pkg_uom)
            line.trixo_pkg_uom_name = pkg_name
            line.trixo_pkg_qty = pkg_qty

    @api.model_create_multi
    def create(self, vals_list):
        """Paridad con 18: en creaciones sin UoM ni cantidad explicitas
        (flujos UI/imports simples), defaultear al embalaje del producto con
        cantidad 1. Si el llamador especifica uom o cantidad, se respeta."""
        for vals in vals_list:
            if (
                vals.get('product_id')
                and 'product_uom_id' not in vals
                and 'product_uom_qty' not in vals
            ):
                product = self.env['product.product'].browse(vals['product_id'])
                uom = self._get_default_packaging_uom(product)
                if uom:
                    vals['product_uom_id'] = uom.id
                    vals['product_uom_qty'] = 1.0
        return super().create(vals_list)

    trixo_price_unit_uom = fields.Float(
        string='Precio Unit.',
        compute='_compute_trixo_price_unit_uom',
        digits='Product Price',
        help='Precio por UNIDAD de producto, no por embalaje.\n\n'
             'En v18 la linea se cargaba en unidades y este era el valor de la '
             'columna "Precio" (ej: 214 por unidad). En v19, tras la conversion '
             'packaging -> UoM, la linea se carga en bultos y price_unit pasa a ser '
             'el precio del bulto (ej: 1.284). Este campo lo reexpresa por unidad '
             'para que el vendedor siga viendo el precio de gondola que le canta al '
             'cliente.',
    )

    @api.depends('price_unit', 'product_uom_id', 'product_id')
    def _compute_trixo_price_unit_uom(self):
        """Precio de la linea reexpresado en la UoM de referencia del producto.

        uom._compute_price devuelve el precio sin cambios cuando las unidades no
        son convertibles entre si (verificado en 19), asi que no hace falta
        validar compatibilidad: en el peor caso muestra el mismo precio.
        """
        for line in self:
            uom = line.product_uom_id
            base = line.product_id.uom_id
            if uom and base and uom != base:
                line.trixo_price_unit_uom = uom._compute_price(line.price_unit, base)
            else:
                line.trixo_price_unit_uom = line.price_unit
