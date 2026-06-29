# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models


class HelpdeskSlaStatus(models.Model):
    _name = 'helpdesk.sla.status'
    _description = 'Helpdesk SLA Status'
    _order = 'deadline, id'

    ticket_id = fields.Many2one(
        'helpdesk.ticket', string='Ticket', required=True,
        ondelete='cascade', index=True)
    sla_id = fields.Many2one(
        'helpdesk.sla', string='SLA Policy', required=True, ondelete='cascade')
    sla_stage_id = fields.Many2one(related='sla_id.stage_id', string='Target Stage')
    deadline = fields.Datetime(
        string='Deadline', compute='_compute_deadline', store=True)
    reached_datetime = fields.Datetime(string='Reached On', copy=False)
    status = fields.Selection([
        ('ongoing', 'In Progress'),
        ('reached', 'Reached'),
        ('failed', 'Failed'),
    ], string='Status', compute='_compute_status', store=True)
    color = fields.Integer(string='Color', compute='_compute_status')

    @api.depends('ticket_id.create_date', 'sla_id.time')
    def _compute_deadline(self):
        for status in self:
            create_date = status.ticket_id.create_date or fields.Datetime.now()
            status.deadline = create_date + timedelta(hours=status.sla_id.time or 0.0)

    @api.depends('deadline', 'reached_datetime')
    def _compute_status(self):
        now = fields.Datetime.now()
        for status in self:
            if status.reached_datetime:
                status.status = 'reached'
                # Late if reached after deadline.
                status.color = 1 if (status.deadline and
                                     status.reached_datetime > status.deadline) else 10
            elif status.deadline and now > status.deadline:
                status.status = 'failed'
                status.color = 1
            else:
                status.status = 'ongoing'
                status.color = 0

    @api.model
    def _cron_check_sla(self):
        """Refresh time-based SLA states for overdue, not-yet-reached lines."""
        overdue = self.search([
            ('reached_datetime', '=', False),
            ('status', '=', 'ongoing'),
            ('deadline', '<', fields.Datetime.now()),
        ])
        if overdue:
            # Force recomputation of the time-dependent stored fields and the
            # dependent ticket counters.
            overdue.modified(['reached_datetime'])
            overdue.flush_recordset()
        return True
