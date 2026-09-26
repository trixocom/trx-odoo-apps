# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        done = moves.filtered(lambda m: m.state == 'done')
        done._trx_check_negative_stock()
        # Un despacho que se valido por otro camino deja sin sentido su solicitud.
        pickings = done.picking_id.filtered(lambda p: p.state == 'done')
        pickings.trx_force_request_ids._cancel_because_picking()
        return moves

    def _trx_check_negative_stock(self):
        """Ultimo control, en la validacion: ningun movimiento que sale de una
        ubicacion interna puede dejar el quant en negativo. Cubre formulario,
        tipeo manual de cantidades, app de codigo de barras, transferencias
        internas y desechos. Excepciones: contexto de aprobacion y despachos
        con solicitud de forzado aprobada."""
        if self.env.context.get('trx_force_approved'):
            return
        Quant = self.env['stock.quant'].sudo()
        problems = []
        seen = set()
        for ml in self.move_line_ids:
            if ml.location_id.usage != 'internal':
                continue
            if not ml.company_id.trx_block_negative_stock:
                continue
            if ml.picking_id and ml.picking_id.trx_force_approved:
                continue
            if not ml.product_id.is_storable:
                continue
            key = (ml.product_id.id, ml.location_id.id, ml.lot_id.id,
                   ml.package_id.id, ml.owner_id.id)
            if key in seen:
                continue
            seen.add(key)
            # Busqueda directa (no _gather): en _action_done puede haber un
            # quants_cache en contexto anterior a la actualizacion.
            domain = Quant._get_gather_domain(
                ml.product_id, ml.location_id, lot_id=ml.lot_id,
                package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
            qty = sum(Quant.search(domain).mapped('quantity'))
            if float_compare(qty, 0, precision_rounding=ml.product_id.uom_id.rounding) < 0:
                problems.append('%s en %s: quedaria %s %s' % (
                    ml.product_id.display_name, ml.location_id.display_name,
                    ('%.2f' % qty).rstrip('0').rstrip('.'), ml.product_id.uom_id.name))
        if problems:
            raise UserError(_(
                'No se puede validar: el stock quedaria negativo.\n%s\n\n'
                'Si la mercaderia esta fisicamente, primero registra el ingreso o la '
                'transferencia; si hay que entregar igual, usa "Solicitar forzar stock".',
                '\n'.join('- ' + p for p in problems)))
