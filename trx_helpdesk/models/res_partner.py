# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    helpdesk_ticket_count = fields.Integer(
        string='Helpdesk Tickets', compute='_compute_helpdesk_ticket_count')

    def _compute_helpdesk_ticket_count(self):
        data = self.env['helpdesk.ticket']._read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'], ['__count'])
        mapped = {partner.id: count for partner, count in data}
        for partner in self:
            partner.helpdesk_ticket_count = mapped.get(partner.id, 0)

    def action_view_helpdesk_tickets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,kanban,form,calendar,pivot,graph,activity',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
