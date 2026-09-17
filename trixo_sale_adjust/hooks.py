# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Tipos de pedido de entrega a domicilio: la mercaderia vuelve despues,
    asi que la devolucion NO se valida automaticamente. Es solo un default
    editable en el form del tipo de pedido."""
    types = env['sale.order.type'].search([('name', 'ilike', 'domicilio')])
    if types:
        types.write({'trixo_adjust_validate_return': False})
        _logger.info(
            'trixo_sale_adjust: devolucion sin validacion automatica en tipos %s',
            types.mapped('name'),
        )
