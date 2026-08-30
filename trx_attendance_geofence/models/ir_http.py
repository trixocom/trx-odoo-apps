# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @api.model
    def lazy_session_info(self):
        """Expone al systray si el empleado tiene geo-barrera exigida, para
        que el JS no ofrezca el «Continuar de todos modos» sin GPS."""
        res = super().lazy_session_info()
        data = res.get('attendance_user_data')
        if data and self.env.user.employee_id:
            data['geofence_required'] = self.env.user.employee_id._geofence_required()
        return res
