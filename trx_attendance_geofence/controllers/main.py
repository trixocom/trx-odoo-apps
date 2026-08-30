# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceGeofence(HrAttendance):

    @http.route('/hr_attendance/systray_check_in_out', type="jsonrpc", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        """Bloquea el fichaje ANTES del relleno con GeoIP cuando el empleado
        tiene geo-barrera y el navegador no mandó coordenadas reales (GPS
        denegado, sin señal o seguimiento de dispositivo desactivado)."""
        employee = request.env.user.with_company(self._get_active_company(request)).employee_id
        if employee and employee._geofence_required() and (not latitude or not longitude):
            raise ValidationError(_(
                "No se pudo obtener tu ubicación. Para registrar el "
                "ingreso/egreso tenés que permitir el acceso a la ubicación "
                "en tu navegador y estar en tu lugar de trabajo.",
            ))
        res = super().systray_attendance(latitude=latitude, longitude=longitude)
        if employee and res:
            res['geofence_required'] = employee._geofence_required()
        return res

    @http.route('/hr_attendance/attendance_user_data', type="jsonrpc", auth="user", readonly=True)
    def user_attendance_data(self):
        res = super().user_attendance_data()
        employee = request.env.user.with_company(self._get_active_company(request)).employee_id
        if employee and res:
            res['geofence_required'] = employee._geofence_required()
        return res
