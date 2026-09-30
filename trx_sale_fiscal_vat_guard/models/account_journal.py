# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    trx_allow_vat_zero = fields.Boolean(
        string="Permitir IVA 0%",
        default=False,
        help="Por defecto, en los diarios de ventas argentinos que usan "
             "documentos fiscales no se puede validar una factura de cliente "
             "con lineas en IVA 0%. Tildar solo si este diario necesita "
             "emitir comprobantes con IVA 0%.",
    )
