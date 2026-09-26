# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    trx_force_request_ids = fields.One2many(
        'stock.force.request', 'picking_id', string='Solicitudes de forzado')
    trx_force_pending_id = fields.Many2one(
        'stock.force.request', string='Solicitud de forzado pendiente',
        compute='_compute_trx_force')
    trx_force_needed = fields.Boolean(
        string='Falta stock', compute='_compute_trx_force',
        help='Hay movimientos sin reservar por falta de stock.')
    trx_force_approved = fields.Boolean(
        string='Forzado aprobado', copy=False, readonly=True,
        help='Un aprobador autorizo entregar este despacho aunque el stock '
             'quede negativo.')

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.quantity',
                 'trx_force_request_ids.state', 'state')
    def _compute_trx_force(self):
        for picking in self:
            pending = picking.trx_force_request_ids.filtered(
                lambda r: r.state in ('draft', 'pending'))[:1]
            picking.trx_force_pending_id = pending
            needed = False
            if picking.state in ('confirmed', 'waiting', 'assigned'):
                for move in picking.move_ids:
                    if move.state in ('done', 'cancel') or not move.product_id.is_storable:
                        continue
                    if float_compare(move.product_uom_qty, move.quantity,
                                     precision_rounding=move.product_uom.rounding) > 0:
                        needed = True
                        break
            picking.trx_force_needed = needed

    # ------------------------------------------------------------------ #
    #  Boton "Solicitar forzar stock"
    # ------------------------------------------------------------------ #
    def action_trx_force_request(self):
        self.ensure_one()
        if self.trx_force_pending_id:
            request = self.trx_force_pending_id
        else:
            request = self.env['stock.force.request']
        return {
            'type': 'ir.actions.act_window',
            'name': _('Solicitar forzar stock'),
            'res_model': 'stock.force.request',
            'view_mode': 'form',
            'res_id': request.id or False,
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'form_view_ref': 'trx_stock_force_request.view_stock_force_request_form',
            },
        }

    # ------------------------------------------------------------------ #
    #  Forzado: solo con aprobacion
    # ------------------------------------------------------------------ #
    def new_force_availability(self):
        """Boton de stock_ux (ADHOC). Fuera de una aprobacion no se puede usar,
        ni desde la vista ni por RPC."""
        if not self.env.context.get('trx_force_approved'):
            raise AccessError(_(
                'Forzar disponibilidad ya no se hace a mano: usa "Solicitar forzar '
                'stock" y espera la aprobacion.'))
        return super().new_force_availability()

    def _trx_force_availability(self, request):
        """Corre el forzado de stock_ux con el contexto de aprobacion y marca el
        despacho para que la validacion posterior no lo rechace por stock negativo."""
        self.ensure_one()
        self.with_context(trx_force_approved=True).new_force_availability()
        if self.state != 'assigned':
            raise UserError(_(
                'No se pudo dejar disponible el despacho %s (estado: %s). Revisalo a mano.',
                self.name, dict(self._fields['state'].selection)[self.state]))
        self.write({'trx_force_approved': True})

    def action_cancel(self):
        res = super().action_cancel()
        self.trx_force_request_ids._cancel_because_picking()
        return res
