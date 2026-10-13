# -*- coding: utf-8 -*-
from odoo import fields, models

from .ir_rule import GROUP_XMLID

#: Campos de costo que un vendedor restringido NO puede leer. Para los campos
#: que en origen eran de base.group_user se conserva esa condición.
COST_GROUPS_INTERNAL = 'base.group_user,!%s' % GROUP_XMLID
COST_GROUPS = '!%s' % GROUP_XMLID


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    trx_restricted_visible = fields.Boolean(
        string='Visible para vendedores restringidos',
        copy=False,
        help='Si está tildado, los usuarios del grupo "Vendedor restringido '
             '(solo CRM)" pueden ver y cotizar este producto. Por defecto '
             'ningún producto es visible para ellos.')

    # product
    standard_price = fields.Float(groups=COST_GROUPS_INTERNAL)
    # product_replenishment_cost
    supplier_price = fields.Float(groups=COST_GROUPS)
    supplier_currency_id = fields.Many2one(groups=COST_GROUPS)
    replenishment_cost = fields.Float(groups=COST_GROUPS)
    replenishment_cost_last_update = fields.Datetime(groups=COST_GROUPS)
    replenishment_base_cost = fields.Float(groups=COST_GROUPS)
    replenishment_base_cost_currency_id = fields.Many2one(groups=COST_GROUPS)
    replenishment_cost_rule_id = fields.Many2one(groups=COST_GROUPS)
    replenishment_base_cost_on_currency = fields.Float(groups=COST_GROUPS)
    replenishment_cost_type = fields.Selection(groups=COST_GROUPS)
    warnings_cost = fields.Json(groups=COST_GROUPS)
    # product_planned_price
    sale_margin = fields.Float(groups=COST_GROUPS)
    sale_surcharge = fields.Float(groups=COST_GROUPS)
    replenishment_cost_main_company = fields.Float(groups=COST_GROUPS)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    standard_price = fields.Float(groups=COST_GROUPS_INTERNAL)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    trx_restricted_visible = fields.Boolean(
        string='Visible para vendedores restringidos',
        copy=False,
        help='Si está tildado, los usuarios del grupo "Vendedor restringido '
             '(solo CRM)" pueden ver y usar esta lista de precios.')
