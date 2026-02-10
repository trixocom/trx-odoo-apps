from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_formula_version = fields.Char(string='Versión de Fórmula')
    x_formula_type = fields.Char(string='Tipo de Fórmula')
    x_min_manufacture_qty = fields.Char(string='Mínimo de Fabricación') # Changed to Char as per Excel "4 KILOS"
    x_elaboration_method = fields.Char(string='Método de Elaboración')
    x_shrinkage = fields.Float(string='Merma', digits=(16, 4))
