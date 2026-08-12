# -*- coding: utf-8 -*-
from odoo import models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def _get_trigger_alarm_types(self):
        """Hacer que las alarmas 'push' agenden el trigger del cron nativo.

        `calendar.event._setup_alarms()` sólo llama a `cron._trigger(at=...)`
        para los tipos que devuelve este método (en el core: ['email'];
        `calendar_sms` le agrega 'sms'). Sin esto, el cron no se despertaría a
        la hora exacta del recordatorio.
        """
        return super()._get_trigger_alarm_types() + ['push']
