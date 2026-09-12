# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License AGPL-3.0
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    trixo_excluir_deudores = fields.Boolean(
        string="Excluir del tablero de Deudores",
        help="Los apuntes por cobrar de este contacto no se muestran en el "
             "tablero de Deudores. Pensado para contactos genericos (mostrador, "
             "consumidor final) que no representan una deuda real de un cliente.",
    )
