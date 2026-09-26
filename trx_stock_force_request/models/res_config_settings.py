# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trx_block_negative_stock = fields.Boolean(
        related='company_id.trx_block_negative_stock', readonly=False)
