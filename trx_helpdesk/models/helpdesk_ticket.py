# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.fields import Datetime

from .helpdesk_sla import TICKET_PRIORITIES


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, id desc'
    _mail_post_access = 'read'

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    @api.model
    def _default_team_id(self):
        team = self.env['helpdesk.team'].search(
            [('member_ids', 'in', self.env.uid)], limit=1)
        if not team:
            team = self.env['helpdesk.team'].search([], limit=1)
        return team

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------
    name = fields.Char(string='Subject', required=True, tracking=True)
    ticket_ref = fields.Char(
        string='Ticket Number', readonly=True, copy=False, index=True,
        default=lambda self: 'New')
    active = fields.Boolean(default=True)
    description = fields.Html(string='Description')
    color = fields.Integer(string='Color')

    team_id = fields.Many2one(
        'helpdesk.team', string='Team', required=True, tracking=True,
        default=lambda self: self._default_team_id(), index=True)
    stage_id = fields.Many2one(
        'helpdesk.stage', string='Stage', tracking=True, index=True,
        store=True, readonly=False, ondelete='restrict',
        compute='_compute_stage_id',
        group_expand='_read_group_stage_ids',
        domain="['|', ('team_ids', '=', False), ('team_ids', 'in', team_id)]")
    user_id = fields.Many2one(
        'res.users', string='Assigned to', tracking=True, index=True,
        domain="['&', ('share', '=', False), ('id', 'in', team_member_ids)]")
    team_member_ids = fields.Many2many(
        'res.users', compute='_compute_team_member_ids',
        string='Team Members (technical)')

    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    partner_name = fields.Char(string='Customer Name')
    partner_email = fields.Char(string='Customer Email')
    partner_phone = fields.Char(string='Customer Phone')

    priority = fields.Selection(
        TICKET_PRIORITIES, string='Priority', default='0', tracking=True, index=True)
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('blocked', 'Blocked'),
        ('done', 'Ready for Next Stage'),
    ], string='Kanban State', default='normal', required=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string='Type')
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)

    # Dates
    assign_date = fields.Datetime(string='Assignment Date', readonly=True, copy=False)
    close_date = fields.Datetime(string='Close Date', readonly=True, copy=False)
    date_last_stage_update = fields.Datetime(
        string='Last Stage Update', readonly=True, copy=False, default=fields.Datetime.now)

    closed = fields.Boolean(
        related='stage_id.is_close', string='Closed', store=True, readonly=True)

    # SLA
    sla_status_ids = fields.One2many(
        'helpdesk.sla.status', 'ticket_id', string='SLA Status', copy=False)
    sla_deadline = fields.Datetime(
        string='SLA Deadline', compute='_compute_sla_deadline', store=True,
        help='Earliest deadline among the SLA policies not yet reached.')
    sla_fail = fields.Boolean(
        string='SLA Failed', compute='_compute_sla_deadline', store=True)

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('team_id')
    def _compute_team_member_ids(self):
        for ticket in self:
            ticket.team_member_ids = ticket.team_id.member_ids

    @api.depends('team_id')
    def _compute_stage_id(self):
        for ticket in self:
            team = ticket.team_id
            stages = team.stage_ids.sorted(lambda s: (s.sequence, s.id))
            if not stages:
                stages = self.env['helpdesk.stage'].search([], order='sequence, id')
            if ticket.stage_id and ticket.stage_id in stages:
                continue
            ticket.stage_id = stages[:1].id if stages else False

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        team_id = self.env.context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('team_ids', '=', False), ('team_ids', 'in', [team_id])]
        else:
            search_domain = []
        stage_ids = stages._search(search_domain, order=stages._order)
        return stages.browse(stage_ids)

    @api.depends('sla_status_ids.deadline', 'sla_status_ids.reached_datetime',
                 'sla_status_ids.status')
    def _compute_sla_deadline(self):
        for ticket in self:
            deadlines = ticket.sla_status_ids.filtered(
                lambda s: not s.reached_datetime and s.deadline).mapped('deadline')
            ticket.sla_deadline = min(deadlines) if deadlines else False
            ticket.sla_fail = any(
                s.status == 'failed' for s in ticket.sla_status_ids)

    # ------------------------------------------------------------------
    # Onchange (UX, mirrors Enterprise behaviour)
    # ------------------------------------------------------------------
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email
            self.partner_phone = self.partner_id.phone

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ticket_ref') or vals['ticket_ref'] == 'New':
                vals['ticket_ref'] = self.env['ir.sequence'].next_by_code(
                    'helpdesk.ticket') or 'New'
            team = self.env['helpdesk.team'].browse(vals.get('team_id')) \
                if vals.get('team_id') else self._default_team_id()
            # Auto-assignment
            if team and not vals.get('user_id'):
                user = team._get_assigned_user()
                if user:
                    vals['user_id'] = user.id
            if vals.get('user_id'):
                vals.setdefault('assign_date', Datetime.now())
        tickets = super().create(vals_list)
        for ticket in tickets:
            if ticket.partner_id and not ticket.partner_name:
                ticket.partner_name = ticket.partner_id.name
            ticket._sla_apply()
            ticket._sla_reach()
        # Follow the assignee
        for ticket in tickets:
            if ticket.user_id:
                ticket.message_subscribe(partner_ids=ticket.user_id.partner_id.ids)
        return tickets

    def write(self, vals):
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = Datetime.now()
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.is_close:
                vals.setdefault('close_date', Datetime.now())
            else:
                vals['close_date'] = False
        res = super().write(vals)
        if 'user_id' in vals and vals['user_id']:
            user = self.env['res.users'].browse(vals['user_id'])
            for ticket in self:
                if not ticket.assign_date:
                    ticket.assign_date = Datetime.now()
            self.message_subscribe(partner_ids=user.partner_id.ids)
        if {'team_id', 'priority', 'ticket_type_id'} & set(vals):
            for ticket in self:
                ticket._sla_apply()
        if 'stage_id' in vals:
            for ticket in self:
                ticket._sla_reach()
        return res

    # ------------------------------------------------------------------
    # SLA engine
    # ------------------------------------------------------------------
    def _matching_slas(self):
        self.ensure_one()
        if not self.team_id.use_sla:
            return self.env['helpdesk.sla']
        domain = [
            ('team_id', '=', self.team_id.id),
            ('priority', '<=', self.priority or '0'),
        ]
        slas = self.env['helpdesk.sla'].search(domain)
        return slas.filtered(
            lambda s: not s.ticket_type_ids
            or self.ticket_type_id in s.ticket_type_ids)

    def _sla_apply(self):
        """Create/remove SLA status lines so they match current ticket data."""
        Status = self.env['helpdesk.sla.status']
        for ticket in self:
            target = ticket._matching_slas()
            existing = ticket.sla_status_ids.mapped('sla_id')
            to_add = target - existing
            to_remove = ticket.sla_status_ids.filtered(
                lambda s: s.sla_id not in target and not s.reached_datetime)
            if to_remove:
                to_remove.unlink()
            for sla in to_add:
                Status.create({'ticket_id': ticket.id, 'sla_id': sla.id})

    def _sla_reach(self):
        """Mark SLA lines as reached when the ticket meets the target stage."""
        for ticket in self:
            current_seq = ticket.stage_id.sequence
            for status in ticket.sla_status_ids:
                if status.reached_datetime:
                    continue
                if ticket.stage_id and current_seq >= status.sla_id.stage_id.sequence:
                    status.reached_datetime = Datetime.now()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------
    def action_assign_to_me(self):
        self.write({'user_id': self.env.uid})

    def action_close(self):
        closing = self.env['helpdesk.stage'].search(
            [('is_close', '=', True)], order='sequence', limit=1)
        if closing:
            self.write({'stage_id': closing.id})
