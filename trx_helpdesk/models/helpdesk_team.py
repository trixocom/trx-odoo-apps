# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'
    _inherit = ['mail.thread']
    _order = 'sequence, name, id'

    name = fields.Char(string='Team Name', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    description = fields.Html(string='Description', translate=True)

    member_ids = fields.Many2many(
        'res.users', 'helpdesk_team_user_rel', 'team_id', 'user_id',
        string='Team Members',
        domain=lambda self: [('share', '=', False)])
    assign_method = fields.Selection([
        ('manual', 'Manually'),
        ('randomly', 'Random'),
        ('balanced', 'Balanced'),
    ], string='Assignment Method', default='manual', required=True,
        help='Manually: tickets are left unassigned.\n'
             'Random: tickets are assigned randomly across members.\n'
             'Balanced: tickets go to the member with the fewest open tickets.')

    stage_ids = fields.Many2many(
        'helpdesk.stage', 'helpdesk_team_stage_rel', 'team_id', 'stage_id',
        string='Stages', default=lambda self: self._default_stage_ids())
    use_sla = fields.Boolean(string='SLA Policies')
    sla_ids = fields.One2many('helpdesk.sla', 'team_id', string='SLA Policies')

    ticket_ids = fields.One2many('helpdesk.ticket', 'team_id', string='Tickets')

    # Dashboard counters
    ticket_count = fields.Integer(string='Open Tickets', compute='_compute_ticket_counts')
    ticket_count_unassigned = fields.Integer(
        string='Unassigned', compute='_compute_ticket_counts')
    ticket_count_urgent = fields.Integer(
        string='Urgent', compute='_compute_ticket_counts')
    ticket_count_sla_fail = fields.Integer(
        string='SLA Failed', compute='_compute_ticket_counts')
    ticket_count_my = fields.Integer(
        string='My Tickets', compute='_compute_ticket_counts')
    ticket_closed_7days = fields.Integer(
        string='Closed (last 7 days)', compute='_compute_performance_7days')
    sla_success_rate = fields.Float(
        string='SLA Success Rate', compute='_compute_performance_7days',
        help='Percentage of tickets closed in the past 7 days whose SLA '
             'targets were all reached on time. -1 when there is no data.')

    @api.model
    def _default_stage_ids(self):
        defaults = self.env['helpdesk.stage']
        for xmlid in ('trx_helpdesk.stage_new',
                      'trx_helpdesk.stage_in_progress',
                      'trx_helpdesk.stage_solved',
                      'trx_helpdesk.stage_cancelled'):
            stage = self.env.ref(xmlid, raise_if_not_found=False)
            if stage:
                defaults |= stage
        if not defaults:
            defaults = self.env['helpdesk.stage'].search([], order='sequence, id')
        return defaults

    def _compute_ticket_counts(self):
        Ticket = self.env['helpdesk.ticket']
        # Open tickets only (not in a closing stage).
        open_data = Ticket._read_group(
            [('team_id', 'in', self.ids), ('closed', '=', False)],
            ['team_id'], ['__count'])
        open_map = {team.id: count for team, count in open_data}

        unassigned_data = Ticket._read_group(
            [('team_id', 'in', self.ids), ('closed', '=', False),
             ('user_id', '=', False)],
            ['team_id'], ['__count'])
        unassigned_map = {team.id: count for team, count in unassigned_data}

        urgent_data = Ticket._read_group(
            [('team_id', 'in', self.ids), ('closed', '=', False),
             ('priority', '=', '3')],
            ['team_id'], ['__count'])
        urgent_map = {team.id: count for team, count in urgent_data}

        sla_data = Ticket._read_group(
            [('team_id', 'in', self.ids), ('closed', '=', False),
             ('sla_fail', '=', True)],
            ['team_id'], ['__count'])
        sla_map = {team.id: count for team, count in sla_data}

        my_data = Ticket._read_group(
            [('team_id', 'in', self.ids), ('closed', '=', False),
             ('user_id', '=', self.env.uid)],
            ['team_id'], ['__count'])
        my_map = {team.id: count for team, count in my_data}

        for team in self:
            team.ticket_count = open_map.get(team.id, 0)
            team.ticket_count_unassigned = unassigned_map.get(team.id, 0)
            team.ticket_count_urgent = urgent_map.get(team.id, 0)
            team.ticket_count_sla_fail = sla_map.get(team.id, 0)
            team.ticket_count_my = my_map.get(team.id, 0)

    def _compute_performance_7days(self):
        """KPIs over the tickets closed within the past 7 days.

        Mirrors the Enterprise dashboard behaviour: the SLA success rate is
        the share of closed tickets (with at least one SLA line) whose SLA
        targets were all reached before their deadline.
        """
        Ticket = self.env['helpdesk.ticket']
        since = fields.Datetime.now() - timedelta(days=7)
        closed_tickets = Ticket.search([
            ('team_id', 'in', self.ids),
            ('closed', '=', True),
            ('close_date', '>=', since),
        ])
        for team in self:
            tickets = closed_tickets.filtered(lambda t: t.team_id == team)
            team.ticket_closed_7days = len(tickets)
            with_sla = tickets.filtered('sla_status_ids')
            if not team.use_sla or not with_sla:
                team.sla_success_rate = -1
                continue
            success = with_sla.filtered(
                lambda t: all(
                    s.reached_datetime and
                    (not s.deadline or s.reached_datetime <= s.deadline)
                    for s in t.sla_status_ids))
            team.sla_success_rate = round(100.0 * len(success) / len(with_sla), 1)

    # ------------------------------------------------------------------
    # Assignment helper used by tickets
    # ------------------------------------------------------------------
    def _get_assigned_user(self):
        """Return the user that should take a new ticket for this team."""
        self.ensure_one()
        members = self.member_ids
        if not members or self.assign_method == 'manual':
            return self.env['res.users']
        if self.assign_method == 'randomly':
            import random
            return random.choice(members)
        # balanced: fewest open tickets
        Ticket = self.env['helpdesk.ticket']
        counts = dict.fromkeys(members.ids, 0)
        data = Ticket._read_group(
            [('team_id', '=', self.id), ('closed', '=', False),
             ('user_id', 'in', members.ids)],
            ['user_id'], ['__count'])
        for user, count in data:
            counts[user.id] = count
        best_id = min(counts, key=counts.get)
        return self.env['res.users'].browse(best_id)

    # ------------------------------------------------------------------
    # Dashboard actions
    # ------------------------------------------------------------------
    def _action_tickets(self, name, extra_domain=None):
        self.ensure_one()
        domain = [('team_id', '=', self.id)]
        if extra_domain:
            domain += extra_domain
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,list,form,calendar,pivot,graph,activity',
            'domain': domain,
            'context': {
                'default_team_id': self.id,
                'search_default_team_id': self.id,
            },
        }

    def action_view_all_tickets(self):
        return self._action_tickets(self.name + ' - Tickets')

    def action_view_open_tickets(self):
        return self._action_tickets(self.name + ' - Open', [('closed', '=', False)])

    def action_view_unassigned(self):
        return self._action_tickets(
            self.name + ' - Unassigned',
            [('closed', '=', False), ('user_id', '=', False)])

    def action_view_urgent(self):
        return self._action_tickets(
            self.name + ' - Urgent',
            [('closed', '=', False), ('priority', '=', '3')])

    def action_view_sla_fail(self):
        return self._action_tickets(
            self.name + ' - SLA Failed',
            [('closed', '=', False), ('sla_fail', '=', True)])

    def action_view_my_tickets(self):
        return self._action_tickets(
            self.name + ' - My Tickets',
            [('closed', '=', False), ('user_id', '=', self.env.uid)])

    def action_view_closed_7days(self):
        since = fields.Datetime.now() - timedelta(days=7)
        action = self._action_tickets(
            self.name + ' - Closed (7 days)',
            [('closed', '=', True), ('close_date', '>=', since)])
        # Closed tickets are better browsed as a list.
        action['view_mode'] = 'list,kanban,form,calendar,pivot,graph,activity'
        return action
