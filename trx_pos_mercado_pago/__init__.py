from . import controllers
from . import models


def pre_init_check(env):
    """No convivir con pos_mercado_pago (core, API deprecada): mismo selector
    de terminal y mismos campos mp_*."""
    from odoo.exceptions import UserError
    core = env['ir.module.module'].search([('name', '=', 'pos_mercado_pago'), ('state', 'in', ('installed', 'to install', 'to upgrade'))])
    if core:
        raise UserError("Desinstale el módulo pos_mercado_pago (core) antes de instalar trx_pos_mercado_pago.")
