from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_formula_version = fields.Char(related='product_id.x_formula_version', string='Versión de Fórmula', readonly=True)
    x_formula_type = fields.Char(related='product_id.x_formula_type', string='Tipo de Fórmula', readonly=True)
    x_min_manufacture_qty = fields.Char(related='product_id.x_min_manufacture_qty', string='Mínimo de Fabricación', readonly=True)
    x_elaboration_method = fields.Char(related='product_id.x_elaboration_method', string='Método de Elaboración', readonly=True)
    x_shrinkage = fields.Float(related='product_id.x_shrinkage', string='Merma', readonly=True)
    
    # We need to ensure that when MO is created, bom_line_id values like phase propagate to stock_move
    # This is handled by Odoo standard: it copies from bom line to stock move IF the field names match? No.
    # We need to override `_get_move_raw_values`.

    def _get_move_raw_values(self, product_id, product_uom_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        res = super()._get_move_raw_values(product_id, product_uom_id, product_uom_qty, product_uom, operation_id, bom_line)
        if bom_line:
            res['x_phase'] = bom_line.x_phase
        return res
