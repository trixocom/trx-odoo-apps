# -*- coding: utf-8 -*-
from odoo import fields, models


class CalendarAlarm(models.Model):
    _inherit = 'calendar.alarm'

    alarm_type = fields.Selection(
        selection_add=[('push', 'Push al celular')],
        ondelete={'push': 'cascade'},
    )
