# -*- coding: utf-8 -*-

from odoo import models

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        modules = super()._get_translation_frontend_modules_name()
        return modules + ['wt_create_so_from_pos']
