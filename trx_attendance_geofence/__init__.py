# -*- coding: utf-8 -*-
from . import models
from . import controllers


def _enable_device_tracking(env):
    """La geo-barrera necesita que el systray mande coordenadas: activa el
    'Device & Location Tracking' de Asistencias en todas las compañías."""
    env['res.company'].sudo().search([]).write({'attendance_device_tracking': True})
