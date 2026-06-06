# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    no_fiscal = fields.Boolean(
        string="No fiscal",
        help="Si esta tildado, al usar este tipo de pedido en una orden de "
             "venta todas las lineas tomaran los impuestos configurados en "
             "'Impuestos No fiscal' (tipicamente IVA 0% / Exento). Si el campo "
             "de impuestos se deja vacio, las lineas quedan sin impuesto.",
    )
    no_fiscal_tax_ids = fields.Many2many(
        comodel_name="account.tax",
        relation="sale_order_type_no_fiscal_tax_rel",
        column1="type_id",
        column2="tax_id",
        string="Impuestos No fiscal",
        domain="[('type_tax_use', '=', 'sale')]",
        check_company=True,
        help="Impuestos que se forzaran en las lineas de la orden cuando "
             "'No fiscal' este tildado. Dejar vacio para quitar todos los "
             "impuestos de las lineas.",
    )
