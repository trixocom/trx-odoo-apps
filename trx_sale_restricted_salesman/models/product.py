from odoo import models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "trx.ocultar.campos.mixin"]
    _trx_campos_ocultos = ("standard_price",)


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "trx.ocultar.campos.mixin"]
    _trx_campos_ocultos = ("standard_price",)
