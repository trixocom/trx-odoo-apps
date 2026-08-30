# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceGeofence(HrAttendance):

    @staticmethod
    def _geofence_check_browser_coords(employee, latitude, longitude, mode=None):
        """Rechaza el fichaje ANTES del relleno con GeoIP del core cuando el
        empleado tiene geo-barrera y el navegador no mandó coordenadas
        reales (GPS denegado, sin señal o seguimiento desactivado)."""
        if employee and employee.sudo()._geofence_required() and (not latitude or not longitude):
            employee.sudo()._geofence_notify_whatsapp(
                result='rechazado',
                detail=_("sin ubicación (GPS denegado o sin señal)"),
                mode=mode)
            raise ValidationError(_(
                "No se pudo obtener tu ubicación. Para registrar el "
                "ingreso/egreso tenés que permitir el acceso a la ubicación "
                "en tu navegador y estar en tu lugar de trabajo.",
            ))

    @http.route('/hr_attendance/manual_selection', type="jsonrpc", auth="public")
    def manual_selection(self, token, employee_id, pin_code, latitude=False, longitude=False):
        company = self._get_company(token)
        if company:
            employee = request.env['hr.employee'].sudo().browse(employee_id).exists()
            if employee and employee.company_id == company:
                self._geofence_check_browser_coords(employee, latitude, longitude, mode='kiosk')
        return super().manual_selection(token, employee_id, pin_code,
                                        latitude=latitude, longitude=longitude)

    @http.route('/hr_attendance/attendance_barcode_scanned', type="jsonrpc", auth="public")
    def scan_barcode_with_geolocation(self, token, barcode, latitude=False, longitude=False):
        company = self._get_company(token)
        if company:
            employee = request.env['hr.employee'].sudo().search(
                [('barcode', '=', barcode), ('company_id', '=', company.id)], limit=1)
            self._geofence_check_browser_coords(employee, latitude, longitude, mode='kiosk')
        return super().scan_barcode_with_geolocation(token, barcode,
                                                     latitude=latitude, longitude=longitude)

    @http.route('/hr_attendance/systray_check_in_out', type="jsonrpc", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        employee = request.env.user.with_company(self._get_active_company(request)).employee_id
        self._geofence_check_browser_coords(employee, latitude, longitude, mode='systray')
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
