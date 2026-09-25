from odoo import fields, models

# El costo nunca visible para el vendedor restringido. Los cálculos de Odoo
# que lo necesitan (listas sobre costo, margen) lo leen como sistema.
GRUPOS_COSTO = "base.group_user,!trx_sale_restricted_salesman.group_restricted_salesman"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(groups=GRUPOS_COSTO)


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(groups=GRUPOS_COSTO)
