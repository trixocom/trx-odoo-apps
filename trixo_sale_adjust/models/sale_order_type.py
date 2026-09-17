# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderType(models.Model):
    _inherit = 'sale.order.type'

    trixo_adjust_validate_return = fields.Boolean(
        string='Validar devolucion al ajustar',
        default=True,
        help='Al ajustar un pedido confirmado de este tipo, la devolucion '
             'de la mercaderia entregada de mas se valida en el acto '
             '(mostrador: la mercaderia esta en mano). Desmarcar para '
             'entregas a domicilio, donde deposito valida cuando vuelve.',
    )
