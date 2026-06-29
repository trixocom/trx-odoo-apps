# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Keep priorities centralised so SLA and ticket stay in sync.
TICKET_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Urgent'),
]


class HelpdeskSla(models.Model):
    _name = 'helpdesk.sla'
    _description = 'Helpdesk SLA Policy'
    _order = 'team_id, time, id'

    name = fields.Char(string='SLA Policy', required=True, translate=True)
    active = fields.Boolean(default=True)
    team_id = fields.Many2one(
        'helpdesk.team', string='Team', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='team_id.company_id', store=True, readonly=True)
    stage_id = fields.Many2one(
        'helpdesk.stage', string='Target Stage', required=True,
        help='The SLA is met once the ticket reaches this stage.')
    priority = fields.Selection(
        TICKET_PRIORITIES, string='Minimum Priority', default='0', required=True,
        help='The policy applies to tickets with at least this priority.')
    ticket_type_ids = fields.Many2many(
        'helpdesk.ticket.type', string='Ticket Types',
        help='Restrict the policy to these types. Leave empty to apply to all.')
    time = fields.Float(
        string='Within (hours)', required=True, default=24.0,
        help='Target time, in hours from ticket creation, to reach the target stage.')
    description = fields.Html(string='Description', translate=True)

    @api.depends('name', 'time')
    def _compute_display_name(self):
        for sla in self:
            sla.display_name = '%s (%gh)' % (sla.name or '', sla.time)
