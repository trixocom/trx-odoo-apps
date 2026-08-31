# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
from odoo import _, http
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.image import image_data_uri

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
                if employee.attendance_excluded:
                    return {}
                self._geofence_check_browser_coords(employee, latitude, longitude, mode='kiosk')
        return super().manual_selection(token, employee_id, pin_code,
                                        latitude=latitude, longitude=longitude)

    @http.route('/hr_attendance/attendance_barcode_scanned', type="jsonrpc", auth="public")
    def scan_barcode_with_geolocation(self, token, barcode, latitude=False, longitude=False):
        company = self._get_company(token)
        if company:
            employee = request.env['hr.employee'].sudo().search(
                [('barcode', '=', barcode), ('company_id', '=', company.id)], limit=1)
            if employee and employee.attendance_excluded:
                return {}
            self._geofence_check_browser_coords(employee, latitude, longitude, mode='kiosk')
        return super().scan_barcode_with_geolocation(token, barcode,
                                                     latitude=latitude, longitude=longitude)

    @http.route('/hr_attendance/attendance_employee_data', type="jsonrpc", auth="public")
    def employee_attendance_data(self, token, employee_id):
        company = self._get_company(token)
        if company:
            employee = request.env['hr.employee'].sudo().browse(employee_id).exists()
            if employee and employee.attendance_excluded:
                return {}
        return super().employee_attendance_data(token, employee_id)

    @http.route('/hr_attendance/employees_infos', type="jsonrpc", auth="public")
    def employees_infos(self, token, limit, offset, domain):
        """Override completo del listado del kiosco para excluir a los
        empleados con «No marca asistencia». El core arma el search adentro
        y valida los campos del domain recibido, así que no se puede
        inyectar el filtro vía super() — se replica la lógica (revisar en
        cada upgrade de Odoo contra hr_attendance/controllers/main.py)."""
        for condition in domain:
            if not isinstance(condition, (list, tuple)) or len(condition) != 3:
                continue
            field_name, operator, _value = condition  # Force '&' implicit syntax
            if field_name not in ('name', 'department_id') or operator not in ('=', 'ilike'):
                raise UserError(_(
                    "Invalid domain, use 'name' and/or 'department_id' fields "
                    "with '=' and/or 'ilike' operators.",
                ))

        company = self._get_company(token)
        if company:
            domain = (Domain(domain)
                      & Domain('company_id', '=', company.id)
                      & Domain('attendance_excluded', '=', False))
            Employee = request.env['hr.employee'].sudo()
            employees = Employee.search_fetch(
                domain, ['id', 'display_name', 'job_id'],
                limit=limit, offset=offset, order="name, id")
            employees_data = [{
                'id': employee.id,
                'display_name': employee.display_name,
                'job_id': employee.job_id.name,
                'avatar': image_data_uri(employee.avatar_128),
                'status': employee.attendance_state,
                'mode': employee.last_attendance_id.in_mode,
            } for employee in employees]
            return {'records': employees_data, 'length': Employee.search_count(domain)}
        return []

    @http.route('/hr_attendance/get_employees_without_badge', type='jsonrpc', auth='public')
    def get_employees_without_badge(self, token, name=None, limit=20):
        """Idem employees_infos: los excluidos tampoco aparecen al asignar
        credenciales desde el kiosco."""
        company = self._get_company(token)
        if company:
            domain = Domain([
                ('barcode', '=', False),
                ('company_id', '=', company.id),
                ('attendance_excluded', '=', False),
            ])
            if name:
                domain = Domain.AND([domain, [('name', 'ilike', name)]])
            employee_list = request.env['hr.employee'].search_read(
                domain,
                ['id', 'name'],
                limit=limit,
            )
            return {'status': 'success', 'employees': employee_list}
        return {}

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
