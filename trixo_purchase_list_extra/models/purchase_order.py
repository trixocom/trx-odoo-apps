from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Prioridad para resolver el estado cuando todavia no hay ninguna recepcion
    # validada: se informa la mas avanzada de las pendientes.
    _TRX_PENDING_PRIORITY = ('assigned', 'confirmed', 'waiting', 'draft')

    trx_receipt_state = fields.Selection(
        selection=[
            ('none', 'Sin recepción'),
            ('draft', 'Borrador'),
            ('waiting', 'En espera de otra operación'),
            ('confirmed', 'En espera'),
            ('assigned', 'Disponible'),
            ('partial', 'Parcial'),
            ('done', 'Hecho'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado de despacho',
        compute='_compute_trx_receipt_state',
        store=True,
        help="Resume el estado de las transferencias de recepción de la orden. "
             "Las canceladas no se tienen en cuenta, salvo que TODAS lo esten.",
    )

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_trx_receipt_state(self):
        for order in self:
            pickings = order.picking_ids
            if not pickings:
                order.trx_receipt_state = 'none'
                continue
            live = pickings.filtered(lambda p: p.state != 'cancel')
            if not live:
                order.trx_receipt_state = 'cancel'
                continue
            done = live.filtered(lambda p: p.state == 'done')
            if len(done) == len(live):
                order.trx_receipt_state = 'done'
                continue
            if done:
                order.trx_receipt_state = 'partial'
                continue
            states = set(live.mapped('state'))
            order.trx_receipt_state = next(
                (state for state in self._TRX_PENDING_PRIORITY if state in states),
                'draft',
            )
