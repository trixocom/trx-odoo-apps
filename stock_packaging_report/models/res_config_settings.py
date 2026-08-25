# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License LGPL-3.0 or later
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    packaging_name_for_stock = fields.Char(
        string='Nombre del Embalaje para Stock',
        config_parameter='stock_packaging_report.packaging_name',
        help='Nombre (o prefijo del nombre) de la unidad de medida de embalaje '
             'del producto que se usa para expresar el stock en bultos.\n'
             'Ejemplo: "Bulto", "Caja", "Pallet".\n\n'
             'En Odoo 19 los embalajes son unidades de medida del producto '
             '(pestana Informacion general > Unidades de medida). El sistema '
             'toma la primera unidad del producto cuyo nombre empiece con este '
             'valor y convierte las cantidades a esa unidad.',
    )
