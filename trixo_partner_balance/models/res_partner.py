# -*- coding: utf-8 -*-
from odoo import models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_open_partner_aml(self):
        """Abre las líneas de asiento del partner filtradas por cuentas
        a cobrar (receivable) o a pagar (payable). Funciona como un
        Partner Ledger simple en Community."""
        self.ensure_one()
        partner_ids = (self | self.child_ids).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ledger de %s') % self.display_name,
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', partner_ids),
                ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('parent_state', '=', 'posted'),
            ],
            'context': {
                'search_default_group_by_account': 1,
                'search_default_unreconciled': 1,
            },
        }
