# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
import math

from odoo import _, fields, models
from odoo.exceptions import ValidationError

# Modos de fichaje sobre los que se aplica la geo-barrera. El kiosco queda
# exento: la tablet/PC del kiosco ya está físicamente en el lugar de trabajo.
GEOFENCE_ENFORCED_MODES = ('systray',)

EARTH_RADIUS_M = 6371000.0


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_geofence_exempt = fields.Boolean(
        string="Exento de geo-barrera",
        groups="hr.group_hr_user",
        help="Si está marcado, este empleado puede fichar desde cualquier "
             "ubicación aunque su ubicación de trabajo tenga geo-barrera "
             "activa (supervisores, personal móvil, etc.).",
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _geofence_distance_m(lat1, lon1, lat2, lon2):
        """Distancia en metros entre dos puntos (fórmula de Haversine)."""
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2.0) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
        return 2.0 * EARTH_RADIUS_M * math.asin(math.sqrt(a))

    def _geofence_location_today(self):
        """Ubicación de trabajo que le corresponde HOY al empleado.

        Con hr_homeworking instalado: excepción del día > ubicación del día
        de la semana > ubicación de trabajo del contrato. Sin homeworking:
        la ubicación de trabajo del contrato (work_location_id).
        """
        self.ensure_one()
        employee = self.sudo()
        location = False
        if 'exceptional_location_id' in employee._fields:
            # hr_homeworking instalado
            location = employee.exceptional_location_id
            if not location:
                location = employee[employee._get_current_day_location_field()]
        if not location:
            location = employee.work_location_id
        return location

    def _geofence_required(self):
        """True si a este empleado se le exige la geo-barrera al fichar."""
        self.ensure_one()
        if self.sudo().attendance_geofence_exempt:
            return False
        location = self._geofence_location_today()
        return bool(location and location.geofence_enabled)

    def _geofence_validate(self, latitude, longitude):
        """Valida que (latitude, longitude) esté dentro del radio de la
        ubicación de trabajo del día. Lanza ValidationError si no."""
        self.ensure_one()
        location = self._geofence_location_today().sudo()
        if not latitude or not longitude:
            raise ValidationError(_(
                "No se pudo obtener tu ubicación. Para registrar el "
                "ingreso/egreso tenés que permitir el acceso a la ubicación "
                "en tu navegador y estar en «%(location)s».",
                location=location.name,
            ))
        distance = self._geofence_distance_m(
            latitude, longitude, location.latitude, location.longitude)
        if distance > location.geofence_radius:
            raise ValidationError(_(
                "Estás a %(distance)s m de «%(location)s» y el fichaje solo "
                "se permite dentro de un radio de %(radius)s m. Acercate a "
                "tu lugar de trabajo para registrar el ingreso/egreso.",
                distance=int(round(distance)),
                location=location.name,
                radius=location.geofence_radius,
            ))

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def _attendance_action_change(self, geo_information=None):
        """Aplica la geo-barrera antes de crear/cerrar la asistencia.

        Solo se valida en los modos alcanzados (systray). El kiosco y los
        registros creados manualmente por RRHH no pasan por acá con esos
        modos y quedan exentos.
        """
        self.ensure_one()
        mode = (geo_information or {}).get('mode')
        if mode in GEOFENCE_ENFORCED_MODES and self._geofence_required():
            self._geofence_validate(
                geo_information.get('latitude'),
                geo_information.get('longitude'),
            )
        return super()._attendance_action_change(geo_information=geo_information)
