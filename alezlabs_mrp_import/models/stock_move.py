from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_phase = fields.Char(string='Fase')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super()._prepare_merge_moves_distinct_fields()
        res.append('x_phase')
        return res

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        # Ensure Phase is propagated if needed logic here (usually mostly for MO -> Picking)
        return res
