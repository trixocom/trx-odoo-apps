from odoo import models, fields

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    x_phase = fields.Char(string='Fase')
