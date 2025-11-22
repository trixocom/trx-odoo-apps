# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class PosConfig(models.Model):
    _inherit = "pos.config"

    create_so = fields.Boolean("Crear Orden de Venta", help="Permitir crear Órdenes de Venta en el PdV", default=True)
