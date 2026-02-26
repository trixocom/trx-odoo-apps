# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    packaging_name_for_stock = fields.Char(
        string='Nombre del Embalaje para Stock',
        config_parameter='stock_packaging_report.packaging_name',
        help='Especifica el nombre del tipo de embalaje (del campo "name" en product.packaging) '
             'que se utilizará para calcular la cantidad de embalajes en stock.\n'
             'Ejemplo: "Caja", "Pallet", "Bulto", etc.\n\n'
             'El sistema buscará este nombre en los embalajes configurados para cada producto '
             'y usará su cantidad (qty) para dividir el stock disponible.'
    )
