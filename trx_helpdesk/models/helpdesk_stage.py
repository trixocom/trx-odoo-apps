# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HelpdeskStage(models.Model):
    _name = 'helpdesk.stage'
    _description = 'Helpdesk Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage', required=True, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='Tickets in a folded stage are shown collapsed in the Kanban view.')
    is_close = fields.Boolean(
        string='Closing Stage',
        help='Tickets reaching this stage are considered solved/closed.')
    team_ids = fields.Many2many(
        'helpdesk.team', 'helpdesk_team_stage_rel', 'stage_id', 'team_id',
        string='Teams',
        help='Teams that use this stage. Leave empty to make it available everywhere.')
    description = fields.Html(string='Stage Description', translate=True)
    active = fields.Boolean(default=True)

    def unlink(self):
        tickets = self.env['helpdesk.ticket'].with_context(active_test=False).search(
            [('stage_id', 'in', self.ids)], limit=1)
        if tickets:
            # Archive instead of breaking referential integrity for in-use stages.
            return self.write({'active': False})
        return super().unlink()
