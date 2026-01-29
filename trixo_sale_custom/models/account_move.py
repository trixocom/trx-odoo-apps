from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ar_latam_document_internal_type = fields.Selection(
        related='l10n_latam_document_type_id.internal_type',
        string='Latam Document Internal Type',
        readonly=True
    )
    trixo_show_print_button = fields.Boolean(
        compute='_compute_trixo_show_print_button',
        string='Show Print Button'
    )
    
    @api.depends('state', 'payment_state', 'sale_type_id')
    def _compute_trixo_show_print_button(self):
        for move in self:
            if move.sale_type_id.id == 6:
                # Exception: Always show for 'Entrega a Domicilio' (even if unpaid)
                move.trixo_show_print_button = True
            elif move.sale_type_id.id == 1:
                # Existing restriction: Hide for ID 1
                move.trixo_show_print_button = False
            else:
                # Default: Show only if Posted AND Paid
                move.trixo_show_print_button = (move.state == 'posted' and move.payment_state == 'paid')
