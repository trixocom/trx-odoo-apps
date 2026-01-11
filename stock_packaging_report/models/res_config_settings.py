# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    packaging_name_for_stock = fields.Char(
        string='Nombre del Embalaje para Stock',
        config_parameter='stock_packaging_report.packaging_name',
        help='Especifica el nombre/categoría de la UoM (antes Packaging) '
             'que se utilizará para calcular la cantidad de embalajes en stock.\n'
             'Ejemplo: "Caja", "Pallet", "Bulto", etc.\n\n'
             'El sistema buscará este nombre en las UoM configuradas '
             'y usará su Factor Inverso para dividir el stock disponible.'
    )
