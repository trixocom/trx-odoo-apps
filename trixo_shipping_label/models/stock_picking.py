from odoo import models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('partner_id')
    def _onchange_partner_id_carrier(self):
        if self.partner_id and self.partner_id.property_delivery_carrier_id:
            self.carrier_id = self.partner_id.property_delivery_carrier_id
