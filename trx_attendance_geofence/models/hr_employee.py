# -*- coding: utf-8 -*-
# Part of Trixocom. See LICENSE file for full copyright and licensing details.
import logging
import math

import pytz

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

NOTIFY_NUMBER_PARAM = 'trx_attendance_geofence.notify_number'
AR_TZ = 'America/Argentina/Buenos_Aires'

# Modos de fichaje sobre los que se aplica la geo-barrera. Se valida tanto
# el systray como el kiosco: el kiosco se usa como link en el celular de
# cada empleado, así que también tiene que respetar la barrera (un kiosco
# físico dentro del radio pasa la validación igual).
GEOFENCE_ENFORCED_MODES = ('systray', 'kiosk')

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
    attendance_excluded = fields.Boolean(
        string="No marca asistencia",
        groups="hr.group_hr_user",
        help="Si está marcado, este empleado no registra asistencia: no "
             "aparece en el listado del kiosco y el servidor le rechaza "
             "cualquier intento de fichaje (dueños, socios, etc.). RRHH "
             "igual puede cargarle asistencias a mano.",
    )
    attendance_notify_channel_id = fields.Many2one(
        'discuss.channel',
        string="Canal de avisos de asistencia",
        groups="hr.group_hr_user",
        help="Canal de WhatsApp (contacto o grupo) al que se mandan los "
             "avisos de ingreso/egreso de ESTE empleado. Si queda vacío, "
             "los avisos van al número general configurado en el parámetro "
             "de sistema trx_attendance_geofence.notify_number.",
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
            self._geofence_notify_whatsapp(
                result='rechazado',
                detail=_("sin ubicación (GPS denegado o sin señal); "
                         "debía estar en «%(location)s»", location=location.name))
            raise ValidationError(_(
                "No se pudo obtener tu ubicación. Para registrar el "
                "ingreso/egreso tenés que permitir el acceso a la ubicación "
                "en tu navegador y estar en «%(location)s».",
                location=location.name,
            ))
        distance = self._geofence_distance_m(
            latitude, longitude, location.latitude, location.longitude)
        if distance > location.geofence_radius:
            self._geofence_notify_whatsapp(
                result='rechazado',
                detail=_("fuera de radio: a %(distance)s m de «%(location)s» "
                         "(radio %(radius)s m)",
                         distance=int(round(distance)), location=location.name,
                         radius=location.geofence_radius),
                latitude=latitude, longitude=longitude)
            raise ValidationError(_(
                "Estás a %(distance)s m de «%(location)s» y el fichaje solo "
                "se permite dentro de un radio de %(radius)s m. Acercate a "
                "tu lugar de trabajo para registrar el ingreso/egreso.",
                distance=int(round(distance)),
                location=location.name,
                radius=location.geofence_radius,
            ))
        return distance, location

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def _attendance_action_change(self, geo_information=None):
        """Aplica la geo-barrera antes de crear/cerrar la asistencia.

        Se valida en los modos alcanzados (systray y kiosco). Los registros
        creados/editados manualmente por RRHH no pasan por acá y quedan
        exentos.
        """
        self.ensure_one()
        mode = (geo_information or {}).get('mode')
        detail = False
        if mode in GEOFENCE_ENFORCED_MODES and self.sudo().attendance_excluded:
            raise ValidationError(_(
                "%(name)s no tiene habilitado el registro de asistencia.",
                name=self.sudo().name,
            ))
        if mode in GEOFENCE_ENFORCED_MODES:
            if self._geofence_required():
                distance, location = self._geofence_validate(
                    geo_information.get('latitude'),
                    geo_information.get('longitude'),
                )
                detail = _("dentro del radio: a %(distance)s m de "
                           "«%(location)s» (radio %(radius)s m)",
                           distance=int(round(distance)),
                           location=location.name,
                           radius=location.geofence_radius)
            elif self.sudo().attendance_geofence_exempt:
                detail = _("exento de geo-barrera")
            else:
                detail = _("sin geo-barrera configurada")
        attendance = super()._attendance_action_change(geo_information=geo_information)
        if detail:
            action = _("EGRESO") if attendance.check_out else _("INGRESO")
            self._geofence_notify_whatsapp(
                result='ok', detail=detail, action=action,
                latitude=(geo_information or {}).get('latitude'),
                longitude=(geo_information or {}).get('longitude'),
                mode=mode)
        return attendance

    # ------------------------------------------------------------------
    # Notificación por WhatsApp (trixo_whatsapp, dependencia blanda)
    # ------------------------------------------------------------------
    def _geofence_notify_whatsapp(self, result, detail, action=None,
                                  latitude=False, longitude=False, mode=None):
        """Manda un WhatsApp con el evento de fichaje al número configurado
        en el parámetro de sistema trx_attendance_geofence.notify_number.

        Dependencia blanda de trixo_whatsapp: si no está instalado o falla
        el envío, se loguea y el fichaje sigue como si nada — la
        notificación nunca puede romper el ingreso/egreso.
        """
        self.ensure_one()
        try:
            env = self.env
            if 'whatsapp.account' not in env:
                return

            # Destino: canal propio del empleado (contacto o grupo) o, si no
            # tiene, el número general del parámetro de sistema.
            channel = False
            notify_channel = self.sudo().attendance_notify_channel_id
            if notify_channel:
                if notify_channel.wa_account_id:
                    channel = notify_channel
                else:
                    _logger.warning(
                        "Geo-barrera: el canal de avisos %r de %s no es un "
                        "canal de WhatsApp; se usa el número general",
                        notify_channel.display_name, self.sudo().name)
            if not channel:
                number = env['ir.config_parameter'].sudo().get_param(NOTIFY_NUMBER_PARAM)
                if not number:
                    return
            account = env['whatsapp.account'].sudo().search([], limit=1)
            if not account:
                _logger.warning("Geo-barrera: no hay cuenta de WhatsApp configurada")
                return

            now_ar = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(
                pytz.timezone(AR_TZ))
            employee = self.sudo()
            icon = "✅" if result == 'ok' else "⛔"
            title = action or _("FICHAJE RECHAZADO")
            lines = [
                "%s %s — %s" % (icon, title, employee.name),
                now_ar.strftime("%d/%m/%Y %H:%M"),
                _("Resultado: %s", detail),
            ]
            if mode == 'kiosk':
                lines.append(_("Origen: kiosco"))
            elif mode == 'systray':
                lines.append(_("Origen: navegador"))
            if latitude and longitude:
                lines.append(_("Ubicación: https://maps.google.com?q=%(lat)s,%(lng)s",
                               lat=latitude, lng=longitude))
            else:
                lines.append(_("Ubicación: no informada"))
            body = "\n".join(lines)

            if not channel:
                from odoo.addons.trixo_whatsapp.drivers.base import normalize_ar_number
                channel = env['discuss.channel'].sudo()._get_or_create_whatsapp_channel(
                    account, normalize_ar_number(number), _("Control de asistencia"))
            channel.sudo().message_post(
                body=body,
                message_type="comment",
                author_id=env.ref('base.partner_root').id,
            )
        except Exception:
            _logger.exception(
                "Geo-barrera: falló la notificación por WhatsApp del fichaje "
                "de %s", self.sudo().name)
