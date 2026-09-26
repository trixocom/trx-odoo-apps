# -*- coding: utf-8 -*-
import logging

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare, plaintext2html

_logger = logging.getLogger(__name__)

GROUP_APPROVER = 'trx_stock_force_request.group_force_approver'


class StockForceRequest(models.Model):
    _name = 'stock.force.request'
    _description = 'Solicitud de forzado de stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Numero', readonly=True, copy=False, default='Nuevo')
    company_id = fields.Many2one(
        'res.company', related='picking_id.company_id', store=True, readonly=True)
    picking_id = fields.Many2one(
        'stock.picking', string='Despacho', required=True, index=True,
        ondelete='cascade', readonly=True)
    picking_type_id = fields.Many2one(
        related='picking_id.picking_type_id', store=True, readonly=True)
    picking_state = fields.Selection(related='picking_id.state', readonly=True)
    origin = fields.Char(related='picking_id.origin', string='Documento origen', readonly=True)
    partner_ref_id = fields.Many2one(
        'res.partner', related='picking_id.partner_id', string='Cliente', readonly=True)
    requester_id = fields.Many2one(
        'res.users', string='Solicita', required=True, readonly=True,
        default=lambda self: self.env.user)
    approver_id = fields.Many2one(
        'res.users', string='Aprueba', readonly=True, tracking=True,
        help='Aprobador al que se dirige la solicitud. Vacio: todos los usuarios '
             'del grupo "Aprobar forzado de stock".')
    partner_id = fields.Many2one(
        'res.partner', string='Contacto del aprobador',
        related='approver_id.partner_id', readonly=True)
    reason = fields.Text(
        string='Motivo', required=True,
        help='Por que hay que entregar sin stock en el sistema: mercaderia en '
             'mano sin ingresar, transferencia pendiente, etc.')
    photo = fields.Image(string='Foto', max_width=1600, max_height=1600, attachment=True)
    line_ids = fields.One2many(
        'stock.force.request.line', 'request_id', string='Faltantes', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente de aprobacion'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='draft', readonly=True, copy=False, tracking=True, index=True)
    request_date = fields.Datetime(string='Enviada', readonly=True, copy=False)
    decision_date = fields.Datetime(string='Decidida', readonly=True, copy=False)
    decision_note = fields.Text(
        string='Respuesta del aprobador',
        help='Obligatoria para rechazar. Se le muestra al que pidio.')
    whatsapp_info = fields.Char(string='WhatsApp', readonly=True, copy=False)
    is_approver = fields.Boolean(compute='_compute_is_approver')

    # ------------------------------------------------------------------ #
    #  Computes / helpers
    # ------------------------------------------------------------------ #
    @api.depends_context('uid')
    def _compute_is_approver(self):
        is_in_group = self.env.user.has_group(GROUP_APPROVER)
        for rec in self:
            rec.is_approver = is_in_group and (
                not rec.approver_id or rec.approver_id == self.env.user)

    def _get_approver_users(self):
        """Usuarios que reciben y pueden decidir esta solicitud."""
        self.ensure_one()
        if self.approver_id:
            return self.approver_id
        group = self.env.ref(GROUP_APPROVER)
        return group.sudo().all_user_ids.filtered(lambda u: u.active and not u.share)

    def _check_can_decide(self):
        for rec in self:
            if not self.env.user.has_group(GROUP_APPROVER):
                raise AccessError(_(
                    'Solo el grupo "Aprobar forzado de stock" puede aprobar o '
                    'rechazar solicitudes.'))
            if rec.approver_id and rec.approver_id != self.env.user \
                    and not self.env.user.has_group('stock.group_stock_manager'):
                raise AccessError(_(
                    'La solicitud %s esta dirigida a %s.', rec.name, rec.approver_id.name))
            if rec.state != 'pending':
                raise UserError(_('La solicitud %s ya no esta pendiente (%s).',
                                  rec.name, dict(rec._fields['state'].selection)[rec.state]))

    @api.model
    def _prepare_lines_from_picking(self, picking):
        """Snapshot de lo que falta por reservar en cada movimiento."""
        vals = []
        Quant = self.env['stock.quant']
        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            missing = move.product_uom_qty - move.quantity
            if float_compare(missing, 0, precision_rounding=move.product_uom.rounding) <= 0:
                continue
            if not move.product_id.is_storable:
                continue
            quants = Quant.sudo()._gather(move.product_id, picking.location_id)
            on_hand = sum(quants.mapped('quantity'))
            free = sum(quants.mapped('available_quantity'))
            vals.append((0, 0, {
                'move_id': move.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_uom.id,
                'qty_demand': move.product_uom_qty,
                'qty_reserved': move.quantity,
                'qty_missing': missing,
                'qty_on_hand': on_hand,
                'qty_free': free,
                'product_base_uom_id': move.product_id.uom_id.id,
            }))
        return vals

    def _refresh_lines(self):
        for rec in self:
            rec.line_ids.unlink()
            rec.write({'line_ids': self._prepare_lines_from_picking(rec.picking_id)})

    def _missing_summary_html(self):
        self.ensure_one()
        items = []
        for line in self.line_ids:
            items.append(Markup('<li>%s: faltan <b>%s %s</b> (pedido %s, hay %s %s en %s)</li>') % (
                line.product_id.display_name,
                self._fmt(line.qty_missing), line.product_uom_id.name,
                self._fmt(line.qty_demand),
                self._fmt(line.qty_on_hand), line.product_base_uom_id.name,
                self.picking_id.location_id.display_name))
        return Markup('<ul>%s</ul>') % Markup('').join(items) if items else Markup('')

    def _missing_summary_text(self):
        self.ensure_one()
        return '\n'.join(
            '- %s: faltan %s %s (hay %s %s)' % (
                line.product_id.display_name, self._fmt(line.qty_missing),
                line.product_uom_id.name, self._fmt(line.qty_on_hand),
                line.product_base_uom_id.name)
            for line in self.line_ids)

    @staticmethod
    def _fmt(qty):
        return ('%.2f' % qty).rstrip('0').rstrip('.')

    def _photo_attachment(self):
        """ir.attachment que respalda el campo photo (attachment=True)."""
        self.ensure_one()
        return self.env['ir.attachment'].sudo().search([
            ('res_model', '=', self._name), ('res_id', '=', self.id),
            ('res_field', '=', 'photo')], limit=1)

    def _photo_as_attachments(self):
        """Copia de la foto para message_post(attachments=...): el adjunto del
        campo (res_field) no se muestra en el chatter de otro documento."""
        self.ensure_one()
        att = self._photo_attachment()
        if not att:
            return []
        name = 'foto_%s.%s' % (self.name.replace('/', '_'),
                               (att.mimetype or 'image/jpeg').split('/')[-1].replace('jpeg', 'jpg'))
        return [(name, att.raw)]

    def _reason_html(self):
        self.ensure_one()
        return plaintext2html(self.reason or '')

    def _clear_activities(self):
        # activity_unlink/feedback solo tocan las del usuario actual; aca hay
        # una actividad por aprobador y todas dejan de tener sentido.
        self.sudo().activity_ids.unlink()

    def _access_url(self):
        self.ensure_one()
        return '/odoo/action-trx_stock_force_request.action_stock_force_request/%s' % self.id

    # ------------------------------------------------------------------ #
    #  ORM
    # ------------------------------------------------------------------ #
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.force.request') or 'Nuevo'
            picking = self.env['stock.picking'].browse(vals.get('picking_id'))
            if picking and not vals.get('approver_id'):
                vals['approver_id'] = picking.picking_type_id.trx_force_approver_id.id or False
            if picking and not vals.get('line_ids'):
                vals['line_ids'] = self._prepare_lines_from_picking(picking)
        return super().create(vals_list)

    @api.constrains('picking_id', 'state')
    def _check_one_pending_per_picking(self):
        for rec in self.filtered(lambda r: r.state in ('draft', 'pending')):
            other = self.search_count([
                ('picking_id', '=', rec.picking_id.id),
                ('state', 'in', ('draft', 'pending')),
                ('id', '!=', rec.id)])
            if other:
                raise UserError(_(
                    'El despacho %s ya tiene una solicitud de forzado pendiente.',
                    rec.picking_id.name))

    # ------------------------------------------------------------------ #
    #  Acciones
    # ------------------------------------------------------------------ #
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('La solicitud %s ya fue enviada.', rec.name))
            if rec.picking_id.state in ('done', 'cancel'):
                raise UserError(_('El despacho %s ya esta %s.', rec.picking_id.name,
                                  dict(rec.picking_id._fields['state'].selection)[rec.picking_id.state]))
            if not (rec.reason or '').strip():
                raise UserError(_('Escribi el motivo por el que hay que forzar el stock.'))
            rec._refresh_lines()
            if not rec.line_ids:
                raise UserError(_(
                    'El despacho %s no tiene faltantes: comproba disponibilidad y validalo.',
                    rec.picking_id.name))
            approvers = rec._get_approver_users()
            if not approvers:
                raise UserError(_(
                    'No hay ningun usuario en el grupo "Aprobar forzado de stock". '
                    'Avisale al administrador.'))
            rec.write({'state': 'pending', 'request_date': fields.Datetime.now()})
            rec._log_on_picking_submit(approvers)
            rec._notify_approvers(approvers)
        return {'type': 'ir.actions.act_window_close'}

    def action_approve(self):
        self._check_can_decide()
        for rec in self:
            picking = rec.picking_id
            if picking.state in ('done', 'cancel'):
                rec._cancel_because_picking()
                return {
                    'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'type': 'warning', 'sticky': True, 'title': _('Solicitud cancelada'),
                               'message': _('El despacho %s ya esta %s; la solicitud %s se cancelo sola.',
                                            picking.name,
                                            dict(picking._fields['state'].selection)[picking.state],
                                            rec.name),
                               'next': {'type': 'ir.actions.act_window_close'}},
                }
            picking.with_context(trx_force_approved=True)._trx_force_availability(rec)
            rec.write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'decision_date': fields.Datetime.now(),
            })
            rec._clear_activities()
            rec._log_on_picking_decision(approved=True)
            rec._notify_requester(approved=True)
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        self._check_can_decide()
        for rec in self:
            if not (rec.decision_note or '').strip():
                raise UserError(_('Para rechazar escribi la respuesta al que pidio.'))
            rec.write({
                'state': 'rejected',
                'approver_id': self.env.user.id,
                'decision_date': fields.Datetime.now(),
            })
            rec._clear_activities()
            rec._log_on_picking_decision(approved=False)
            rec._notify_requester(approved=False)
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'pending'):
                raise UserError(_('La solicitud %s ya esta decidida.', rec.name))
            if rec.requester_id != self.env.user and not self.env.user.has_group(GROUP_APPROVER):
                raise AccessError(_('Solo el que pidio o un aprobador puede cancelar la solicitud.'))
            rec.write({'state': 'cancelled', 'decision_date': fields.Datetime.now()})
            rec._clear_activities()
            rec.picking_id.message_post(body=_('Solicitud de forzado %s cancelada por %s.',
                                               rec.name, self.env.user.name))
        return {'type': 'ir.actions.act_window_close'}

    def _cancel_because_picking(self):
        """El despacho se valido o cancelo por otro camino: la solicitud ya no aplica."""
        for rec in self.filtered(lambda r: r.state in ('draft', 'pending')):
            rec.write({'state': 'cancelled', 'decision_date': fields.Datetime.now()})
            rec._clear_activities()
            rec.message_post(body=_('Cancelada: el despacho %s ya esta %s.',
                                    rec.picking_id.name,
                                    dict(rec.picking_id._fields['state'].selection)[rec.picking_id.state]))

    @api.model
    def get_pending_for_me(self):
        """Para el servicio JS: solicitudes pendientes que espera el usuario actual."""
        if not self.env.user.has_group(GROUP_APPROVER):
            return []
        recs = self.search([
            ('state', '=', 'pending'),
            '|', ('approver_id', '=', self.env.uid), ('approver_id', '=', False)])
        return [{'id': r.id, 'name': r.name, 'picking': r.picking_id.name} for r in recs]

    # ------------------------------------------------------------------ #
    #  Chatter / notificaciones
    # ------------------------------------------------------------------ #
    def _log_on_picking_submit(self, approvers):
        self.ensure_one()
        body = Markup('<p><b>Solicitud de forzado de stock %s</b> enviada a %s por %s.</p>'
                      '<p><b>Motivo:</b></p>%s%s') % (
            self.name, ', '.join(approvers.mapped('name')), self.requester_id.name,
            self._reason_html(), self._missing_summary_html())
        self.picking_id.message_post(body=body, attachments=self._photo_as_attachments())

    def _log_on_picking_decision(self, approved):
        self.ensure_one()
        if approved:
            body = Markup('<p><b>Forzado de stock APROBADO</b> por %s (solicitud %s de %s).</p>'
                          '<p><b>Motivo:</b></p>%s%s') % (
                self.env.user.name, self.name, self.requester_id.name,
                self._reason_html(), self._missing_summary_html())
            if self.decision_note:
                body += Markup('<p><b>Nota:</b> %s</p>') % self.decision_note
        else:
            body = Markup('<p><b>Forzado de stock RECHAZADO</b> por %s (solicitud %s de %s).</p>'
                          '<p><b>Respuesta:</b> %s</p>') % (
                self.env.user.name, self.name, self.requester_id.name, self.decision_note)
        self.picking_id.message_post(body=body, attachments=self._photo_as_attachments())

    def _bus_payload(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'picking': self.picking_id.name,
            'origin': self.picking_id.origin or '',
            'requester': self.requester_id.name,
            'reason': self.reason,
        }

    def _notify_approvers(self, approvers):
        self.ensure_one()
        body = Markup('<p><b>%s</b> pide forzar stock en <b>%s</b>%s.</p><p><b>Motivo:</b></p>%s%s') % (
            self.requester_id.name, self.picking_id.name,
            (' (%s)' % self.picking_id.origin) if self.picking_id.origin else '',
            self._reason_html(), self._missing_summary_html())
        # Campanita + push del celular (mail: comment a partner_ids -> inbox + web push)
        self.message_post(
            body=body, partner_ids=approvers.partner_id.ids,
            attachments=self._photo_as_attachments(),
            message_type='comment', subtype_xmlid='mail.mt_comment')
        # Actividad para que quede en la lista de pendientes
        for user in approvers:
            self.activity_schedule(
                'mail.mail_activity_data_todo', user_id=user.id,
                summary=_('Aprobar forzado de stock %s', self.picking_id.name),
                note=body)
        # Pop-up en vivo (servicio JS del modulo)
        Bus = self.env['bus.bus']
        for partner in approvers.partner_id:
            Bus._sendone(partner, 'trx_force_request', self._bus_payload())
        # WhatsApp (si trixo_whatsapp esta instalado y hay cuenta conectada)
        self._send_whatsapp(approvers)

    def _notify_requester(self, approved):
        self.ensure_one()
        title = _('Forzado de stock aprobado') if approved else _('Forzado de stock rechazado')
        if approved:
            message = _('%s aprobo tu solicitud %s: el despacho %s ya esta disponible para validar.',
                        self.env.user.name, self.name, self.picking_id.name)
        else:
            message = _('%s rechazo tu solicitud %s sobre %s: %s',
                        self.env.user.name, self.name, self.picking_id.name, self.decision_note)
        self.message_post(
            body=plaintext2html(message), partner_ids=self.requester_id.partner_id.ids,
            message_type='comment', subtype_xmlid='mail.mt_comment')
        self.env['bus.bus']._sendone(self.requester_id.partner_id, 'simple_notification', {
            'title': title,
            'message': message,
            'type': 'success' if approved else 'warning',
            'sticky': True,
        })

    def _send_whatsapp(self, users):
        """Manda la solicitud por WhatsApp con trixo_whatsapp, si esta. Nunca corta el flujo."""
        self.ensure_one()
        if 'whatsapp.compose' not in self.env:
            return
        base_url = self.get_base_url()
        text = _(
            'Solicitud de forzado de stock %(name)s\n'
            'Despacho: %(picking)s%(origin)s\n'
            'Pide: %(requester)s\n'
            'Motivo: %(reason)s\n'
            'Faltantes:\n%(missing)s\n'
            'Aprobar o rechazar: %(url)s',
            name=self.name, picking=self.picking_id.name,
            origin=(' (%s)' % self.picking_id.origin) if self.picking_id.origin else '',
            requester=self.requester_id.name, reason=self.reason,
            missing=self._missing_summary_text(), url=base_url + self._access_url())
        att = self._photo_attachment()
        Compose = self.env['whatsapp.compose']
        results = []
        for user in users:
            partner = user.partner_id
            try:
                with self.env.cr.savepoint():
                    res = Compose.send_from_chatter(
                        'res.partner', partner.id, plaintext2html(text),
                        attachment_ids=att.ids or None)
            except Exception as err:  # noqa: BLE001 - el WA nunca debe frenar la solicitud
                _logger.exception('trx_stock_force_request: WhatsApp a %s fallo', partner.name)
                res = {'error': str(err)}
            if isinstance(res, dict) and res.get('error'):
                results.append('%s: NO enviado (%s)' % (partner.name, res['error']))
            else:
                results.append('%s: enviado' % partner.name)
        info = '; '.join(results)[:250]
        self.write({'whatsapp_info': info})
        self.message_post(body=Markup('<p>WhatsApp: %s</p>') % info)


class StockForceRequestLine(models.Model):
    _name = 'stock.force.request.line'
    _description = 'Faltante de una solicitud de forzado'
    _order = 'id'

    request_id = fields.Many2one(
        'stock.force.request', required=True, ondelete='cascade', index=True)
    move_id = fields.Many2one('stock.move', string='Movimiento', ondelete='set null')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='UdM')
    product_base_uom_id = fields.Many2one('uom.uom', string='UdM base')
    qty_demand = fields.Float(string='Pedido', digits='Product Unit')
    qty_reserved = fields.Float(string='Reservado', digits='Product Unit')
    qty_missing = fields.Float(string='Falta', digits='Product Unit')
    qty_on_hand = fields.Float(string='Stock en origen', digits='Product Unit')
    qty_free = fields.Float(string='Libre en origen', digits='Product Unit')
