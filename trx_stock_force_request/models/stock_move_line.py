# -*- coding: utf-8 -*-
from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _check_manual_lines(self):
        """stock_ux rechaza crear lineas por encima del stock cuando el tipo de
        operacion tiene "Block force availability". Con una solicitud aprobada,
        el forzado tiene que poder crearlas."""
        if self.env.context.get('trx_force_approved'):
            return
        return super()._check_manual_lines()
