# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

PUSH_ALARM_TYPE = 'push'


class CalendarAlarmManager(models.AbstractModel):
    _inherit = 'calendar.alarm_manager'

    @api.model
    def _send_reminder(self):
        """El cron nativo `calendar.ir_cron_scheduler_alarm` entra por acá.

        Primero corre el envío estándar (mails) y después el push. El push va
        dentro de un try/except a propósito: un problema de red contra FCM/APNs
        no puede tumbar los recordatorios por mail ni dejar el cron en error.
        """
        res = super()._send_reminder()
        try:
            self._send_push_reminder()
        except Exception:  # noqa: BLE001
            _logger.exception("trx_calendar_push: falló el envío de recordatorios push")
        return res

    @api.model
    def _send_push_reminder(self):
        Push = self.env.get('trx.web.push.subscription')
        if Push is None:
            _logger.warning("trx_calendar_push: trx_web_push no está disponible, no se envía nada")
            return

        events_by_alarm = self._get_events_by_alarm_to_notify(PUSH_ALARM_TYPE)
        if not events_by_alarm:
            return

        event_ids = list({eid for eids in events_by_alarm.values() for eid in eids})
        events = self.env['calendar.event'].browse(event_ids)
        now = fields.Datetime.now()
        sent = 0

        for alarm in self.env['calendar.alarm'].browse(events_by_alarm.keys()):
            alarm_events = events.filtered(
                lambda ev: ev.id in events_by_alarm[alarm.id] and ev.stop > now
            )
            for event in alarm_events:
                sent += self._push_notify_event(Push, event, alarm)

        # Mantiene vivo el trigger del cron para la próxima ocurrencia de las
        # reuniones recurrentes (mismo comportamiento que el recordatorio mail).
        events._setup_event_recurrent_alarms(events_by_alarm)

        if sent:
            _logger.info("trx_calendar_push: %s recordatorio(s) push enviados", sent)

    def _push_notify_event(self, Push, event, alarm):
        """Envía el push de `event` a cada asistente que corresponda.

        :return: cantidad de usuarios notificados.
        """
        partners = event.attendee_ids.filtered(
            lambda att: att.state != 'declined'
        ).partner_id
        if not partners:
            return 0

        users = self.env['res.users'].sudo().search([
            ('partner_id', 'in', partners.ids),
            ('active', '=', True),
            ('share', '=', False),
        ])
        if not users:
            return 0

        url = '/odoo/calendar.event/%s' % event.id
        sent = 0
        for user in users:
            title, body = self._push_get_payload(event, alarm, user)
            try:
                Push.sudo().send_to_users(user, title, body, url=url)
                sent += 1
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "trx_calendar_push: falló el push del evento %s al usuario %s",
                    event.id, user.login,
                )
        return sent

    def _push_get_payload(self, event, alarm, user):
        """Título y cuerpo de la notificación, en el idioma y huso del usuario."""
        localized = event.with_context(
            tz=user.tz or self.env.user.tz or 'UTC',
            lang=user.lang or self.env.context.get('lang') or 'es_AR',
        )
        lines = [localized.display_time or '']
        if event.location:
            lines.append(self.env._("Lugar: %(location)s", location=event.location))
        if alarm.body:
            lines.append(alarm.body)
        return event.name or self.env._("Reunión"), "\n".join(line for line in lines if line)
