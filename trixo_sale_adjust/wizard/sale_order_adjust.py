# -*- coding: utf-8 -*-
"""Wizard "Ajustar pedido": una sola pantalla para cancelar pendientes,
devolver mercaderia entregada y emitir la nota de credito que corresponda
sobre un pedido confirmado, incluso facturado y cobrado.

Orden de ejecucion (una transaccion):
  1. devoluciones (stock.return.picking core, to_refund=True)
  2. baja de cantidades (el core cancela los movimientos pendientes)
  3. notas de credito (reversion parcial de la factura original via el
     wizard estandar account.move.reversal)
  4. facturas: componentes de combos desarmados (re-tasados) y lo AGREGADO
     al pedido que quedo pendiente de facturar. Diario no fiscal: se
     confirma en el acto. Diario fiscal (l10n_latam_use_documents): queda
     en borrador y se avisa.
  5. conciliacion NC <-> facturas impagas de la orden

Lo agregado (mas cantidad / productos nuevos) se carga en las lineas del
pedido: al guardar, el core genera el despacho adicional, que queda listo
para validar por el circuito normal. El wizard solo reduce y factura.
"""
import logging

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)


class SaleOrderAdjust(models.TransientModel):
    _name = 'sale.order.adjust'
    _description = 'Ajuste de pedido confirmado'

    order_id = fields.Many2one('sale.order', string='Pedido', required=True,
                               readonly=True, ondelete='cascade')
    partner_id = fields.Many2one(related='order_id.partner_id')
    currency_id = fields.Many2one(related='order_id.currency_id')
    reason = fields.Char(
        string='Motivo',
        help='Se registra en el chatter del pedido, de la devolucion y '
             'como referencia de la nota de credito.',
    )
    validate_return = fields.Boolean(
        string='Validar la devolucion ahora',
        help='Marcado: la mercaderia devuelta ingresa al deposito en el acto '
             '(mostrador). Desmarcado: la devolucion queda pendiente para que '
             'deposito la valide cuando la mercaderia vuelve.',
    )
    credit_note_mode = fields.Selection(
        [
            ('post', 'Emitir y confirmar la nota de credito'),
            ('draft', 'Dejar la nota de credito en borrador'),
            ('none', 'No generar nota de credito ahora'),
        ],
        string='Nota de credito', default='post', required=True,
    )
    invoice_added = fields.Boolean(
        string='Facturar lo agregado',
        help='Genera la factura por las cantidades del pedido que todavia no '
             'estan facturadas (productos o cantidades agregadas). Diario no '
             'fiscal: se confirma en el acto. Diario fiscal (AFIP/ARCA): queda '
             'en borrador para revisar y confirmar.',
    )
    prefill_notice = fields.Char(readonly=True)
    line_ids = fields.One2many('sale.order.adjust.line', 'wizard_id', string='Lineas')
    summary_html = fields.Html(string='Resumen', compute='_compute_summary', sanitize=False)
    has_changes = fields.Boolean(compute='_compute_summary')
    has_credit = fields.Boolean(compute='_compute_summary')
    has_return = fields.Boolean(compute='_compute_summary')
    has_invoice = fields.Boolean(compute='_compute_summary')
    has_pending_invoice = fields.Boolean(compute='_compute_summary')
    invoice_is_fiscal = fields.Boolean(compute='_compute_summary')

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'validate_return' not in vals and vals.get('order_id'):
                order = self.env['sale.order'].browse(vals['order_id'])
                sot = order.type_id if 'type_id' in order._fields else False
                vals['validate_return'] = (
                    sot.trixo_adjust_validate_return if sot else True
                )
            if 'invoice_added' not in vals and vals.get('order_id'):
                # Solo por defecto en pedidos que ya se facturaron: en uno que
                # nunca se facturo, lo pendiente sigue el circuito normal
                # ("Crear factura") salvo que el usuario tilde la opcion.
                order = self.env['sale.order'].browse(vals['order_id'])
                vals['invoice_added'] = bool(order.invoice_ids.filtered(
                    lambda m: m.move_type == 'out_invoice' and m.state != 'cancel'))
        return super().create(vals_list)

    def _get_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ajustar pedido %s', self.order_id.name),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _populate_lines(self):
        self.ensure_one()
        Line = self.env['sale.order.adjust.line']
        self.line_ids.unlink()
        vals_list = []
        for sl in self.order_id.order_line.sorted(lambda l: (l.sequence, l.id)):
            if sl.display_type or not sl.product_id:
                continue
            kind = 'normal'
            parent = False
            if sl._trixo_adjust_is_combo_parent():
                kind = 'combo_parent'
            elif 'surtido_parent_line_id' in sl._fields and sl.surtido_parent_line_id:
                kind = 'combo_child'
                parent = sl.surtido_parent_line_id.id
            vals_list.append({
                'wizard_id': self.id,
                'sale_line_id': sl.id,
                'sequence': sl.sequence,
                'kind': kind,
                'combo_parent_line_id': parent,
                'ordered_qty': sl.product_uom_qty,
                'delivered_qty': sl.qty_delivered,
                'invoiced_qty': sl.qty_invoiced,
                'new_qty': sl.product_uom_qty,
                'locked': kind == 'combo_parent' or sl.is_downpayment,
            })
        Line.create(vals_list)
        self._compute_lines_from_new_qty()

    def _apply_requested_quantities(self, requested):
        """Carga en "Nueva cantidad" lo que el usuario bajo en las lineas del
        pedido antes de apretar "Ajustar pedido" (ver adjust_button_patch.js).
        `requested`: {id de sale.order.line (int o str): cantidad}."""
        self.ensure_one()
        if not requested or not isinstance(requested, dict):
            return
        precision = self._uom_precision()
        by_line = {wl.sale_line_id.id: wl for wl in self.line_ids}
        taken, skipped = 0, []
        for key, qty in requested.items():
            try:
                line_id, qty = int(key), float(qty)
            except (TypeError, ValueError):
                continue
            wl = by_line.get(line_id)
            if not wl:
                continue
            if wl.locked:
                skipped.append(wl.sale_line_id.product_id.display_name)
                continue
            if qty < 0 or float_compare(qty, wl.ordered_qty, precision_digits=precision) >= 0:
                continue
            wl.new_qty = qty
            taken += 1
        notice = []
        if taken:
            notice.append(_('Se tomaron del pedido las cantidades de %s linea(s).', taken))
        if skipped:
            notice.append(_(
                'No se tomo la cantidad de: %s (cabecera de combo o anticipo: '
                'ajusta los componentes).', ', '.join(skipped)))
        self.prefill_notice = ' '.join(notice) or False
        self._compute_lines_from_new_qty()

    def action_set_all_delivered(self):
        """Equivalente al wizard "cancelar remanente" de v18: todas las
        lineas quedan en lo entregado."""
        self.ensure_one()
        for wl in self.line_ids.filtered(lambda l: not l.locked):
            wl.new_qty = min(wl.ordered_qty, wl.delivered_qty)
        self._compute_lines_from_new_qty()
        return self._get_action()

    # ------------------------------------------------------------------
    # Plan (preview) — se recalcula con cada cambio de "Nueva cantidad"
    # ------------------------------------------------------------------
    @api.onchange('line_ids', 'invoice_added')
    def _onchange_line_ids(self):
        self._compute_lines_from_new_qty()

    def _uom_precision(self):
        return self.env['decimal.precision'].precision_get('Product Unit')

    def _combo_factor(self, parent_sl, new_qty_by_line):
        """Re-evalua el combo con la receta del surtido y las cantidades
        nuevas de los componentes. Devuelve la cantidad de combos que
        siguen aplicando (0 si el combo se desarma). Espeja la logica de
        `sale.order._match_surtido_partial` del modulo de surtidos:
        bultos por grupo // required_qty, minimo entre grupos."""
        order = self.order_id
        surtido = parent_sl.surtido_id
        if not surtido or not surtido.group_ids:
            return 0
        children = parent_sl._trixo_adjust_combo_children()
        product_to_group = order._build_product_to_group_map(surtido)
        totals = {g.id: 0.0 for g in surtido.group_ids}
        for child in children:
            gid = product_to_group.get(child.product_id.id)
            if not gid:
                continue
            cur_bultos = order._surtido_line_bultos(child)
            if child.product_uom_qty and cur_bultos:
                ratio = cur_bultos / child.product_uom_qty
            else:
                ratio = 0.0
            totals[gid] += ratio * new_qty_by_line.get(child, child.product_uom_qty)
        factors = []
        for group in surtido.group_ids:
            total = totals.get(group.id, 0.0)
            if total <= 0 or group.required_qty <= 0:
                return 0
            factors.append(int(total // group.required_qty))
        return min(factors) if factors else 0

    def _compute_lines_from_new_qty(self):
        precision = self._uom_precision()
        for wizard in self:
            lines = wizard.line_ids
            cmp = lambda a, b: float_compare(a, b, precision_digits=precision)  # noqa: E731

            # --- combos: decidir si se desarman -------------------------
            dissolve_parents = set()
            for p in lines.filtered(lambda l: l.kind == 'combo_parent'):
                children = lines.filtered(lambda l: l.combo_parent_line_id == p.sale_line_id)
                if not any(cmp(c.new_qty, c.ordered_qty) != 0 for c in children):
                    continue
                factor_new = wizard._combo_factor(
                    p.sale_line_id, {c.sale_line_id: c.new_qty for c in children},
                )
                if cmp(factor_new, p.ordered_qty) < 0:
                    dissolve_parents.add(p.sale_line_id.id)

            for wl in lines:
                sl = wl.sale_line_id
                has_stock = sl.qty_delivered_method == 'stock_move'
                ordered, delivered, invoiced = wl.ordered_qty, wl.delivered_qty, wl.invoiced_qty
                new = wl.new_qty
                wl.combo_dissolve = False
                wl.release_from_combo = False
                wl.reinvoice_qty = 0.0
                if wl.kind == 'combo_parent':
                    if sl.id in dissolve_parents:
                        wl.combo_dissolve = True
                        wl.target_qty = 0.0
                        wl.return_qty = delivered if has_stock else 0.0
                        wl.cancel_qty = max(ordered - delivered, 0.0)
                        wl.credit_qty = invoiced
                    else:
                        wl.target_qty = ordered
                        wl.return_qty = wl.cancel_qty = wl.credit_qty = 0.0
                    wl.new_qty = wl.target_qty
                elif wl.kind == 'combo_child' and wl.combo_parent_line_id.id in dissolve_parents:
                    wl.combo_dissolve = True
                    wl.release_from_combo = True
                    wl.target_qty = new
                    wl.return_qty = max(delivered - new, 0.0) if has_stock else 0.0
                    wl.cancel_qty = max(ordered - max(new, delivered), 0.0)
                    wl.credit_qty = invoiced           # a $0: libera qty_invoiced
                    wl.reinvoice_qty = new             # a precio de lista vigente
                else:
                    wl.target_qty = new
                    wl.return_qty = max(delivered - new, 0.0) if has_stock else 0.0
                    wl.cancel_qty = max(ordered - max(new, delivered), 0.0)
                    wl.credit_qty = max(invoiced - new, 0.0)
                # Pendiente de facturar (lo agregado al pedido). Los combos
                # que se desarman van por `reinvoice_qty`.
                wl.pending_invoice_qty = 0.0
                if not wl.combo_dissolve and not sl.is_downpayment:
                    base = wl.target_qty
                    if sl.product_id.invoice_policy == 'delivery':
                        base = min(wl.target_qty, delivered)
                    wl.pending_invoice_qty = max(base - invoiced, 0.0)
                wl.invoice_qty = wl.pending_invoice_qty if wizard.invoice_added else 0.0
                for f in ('return_qty', 'cancel_qty', 'credit_qty', 'reinvoice_qty',
                          'target_qty', 'invoice_qty', 'pending_invoice_qty'):
                    wl[f] = float_round(wl[f], precision_digits=precision)
                wl.has_action = bool(
                    cmp(wl.return_qty, 0) > 0 or cmp(wl.cancel_qty, 0) > 0
                    or cmp(wl.credit_qty, 0) > 0 or cmp(wl.reinvoice_qty, 0) > 0
                    or cmp(wl.invoice_qty, 0) > 0 or cmp(wl.swap_qty, 0) > 0
                    or wl.release_from_combo or cmp(wl.target_qty, ordered) != 0
                )
                wl.action_summary = wl._build_action_summary()

    @api.depends('line_ids.new_qty', 'line_ids.action_summary', 'credit_note_mode',
                 'validate_return', 'invoice_added')
    def _compute_summary(self):
        for wizard in self:
            lines = wizard.line_ids.filtered('has_action')
            wizard.has_changes = bool(lines)
            wizard.has_return = any(l.return_qty > 0 for l in lines)
            wizard.has_credit = any(l.credit_qty > 0 for l in lines)
            wizard.has_invoice = any(l.invoice_qty > 0 for l in lines)
            wizard.has_pending_invoice = any(
                l.pending_invoice_qty > 0 for l in wizard.line_ids)
            wizard.invoice_is_fiscal = bool(
                wizard.has_pending_invoice and wizard._added_invoice_is_fiscal())
            if not lines:
                wizard.summary_html = _('<i>Sin cambios: baja la columna "Nueva cantidad" y, si el cliente se lleva otro embalaje a cambio, carga "Se lleva".</i>')
                continue
            parts = []
            n_ret = sum(1 for l in lines if l.return_qty > 0)
            n_cancel = sum(1 for l in lines if l.cancel_qty > 0)
            n_credit = sum(1 for l in lines if l.credit_qty > 0)
            n_combo = len({l.combo_parent_line_id.id or l.sale_line_id.id for l in lines if l.combo_dissolve})
            if n_cancel:
                parts.append(_('%s linea(s) con pendiente a cancelar', n_cancel))
            if n_ret:
                parts.append(_('devolucion en %s linea(s)%s', n_ret,
                               _(' (se valida ahora)') if wizard.validate_return else _(' (queda pendiente para deposito)')))
            if n_credit:
                mode = dict(wizard._fields['credit_note_mode'].selection)[wizard.credit_note_mode]
                parts.append(_('nota de credito sobre %s linea(s) — %s', n_credit, mode.lower()))
            if n_combo:
                parts.append(_('%s combo(s) se desarma(n): NC por la cabecera y componentes '
                               'facturados a precio de lista', n_combo))
            n_swap = sum(1 for l in lines if l.swap_qty > 0)
            if n_swap:
                parts.append(_('%s linea(s) con cambio de embalaje: se factura lo que el '
                               'cliente se lleva, al precio de lista del embalaje nuevo', n_swap))
            n_inv = sum(1 for l in lines if l.invoice_qty > 0)
            if n_inv:
                parts.append(_('factura por lo agregado en %s linea(s)%s', n_inv,
                               _(' — diario fiscal: queda en BORRADOR para revisar y confirmar')
                               if wizard.invoice_is_fiscal else _(' — se confirma ahora')))
            wizard.summary_html = '<ul>' + ''.join('<li>%s</li>' % p for p in parts) + '</ul>'

    # ------------------------------------------------------------------
    # Ejecucion
    # ------------------------------------------------------------------
    def action_apply(self):
        self.ensure_one()
        order = self.order_id
        order._trixo_adjust_check_order()
        if not (self.reason or '').strip():
            raise UserError(_('Indica el motivo del ajuste.'))
        self._compute_lines_from_new_qty()
        self._check_plan()
        plan = self.line_ids.filtered('has_action')
        if not plan:
            raise UserError(_('No hay cambios para aplicar.'))

        ctx_lines = plan.with_context(skip_surtido_detection=True)
        returns = self._do_returns(ctx_lines)
        self._do_quantities(ctx_lines)
        refunds, refund_errors = self._do_credit_notes(ctx_lines)
        swapped = self._do_swaps(ctx_lines)
        invoices, invoice_errors = self._do_reinvoice(ctx_lines, extra_lines=swapped)
        self._do_reconcile(refunds, invoices)
        self._post_messages(plan, returns, refunds, invoices, refund_errors + invoice_errors)

        errors = refund_errors + invoice_errors
        msg = _('Ajuste aplicado sobre %s.', order.name)
        if returns:
            msg += ' ' + _('Devoluciones: %s.', ', '.join(returns.mapped('name')))
        if refunds:
            msg += ' ' + _('Notas de credito: %s.', ', '.join(
                m.name if m.state == 'posted' else _('%s (borrador)', m.display_name) for m in refunds))
        if invoices:
            msg += ' ' + _('Facturas: %s.', ', '.join(
                m.name if m.state == 'posted' else _('%s (borrador)', m.display_name) for m in invoices))
        if errors:
            msg += ' ' + _('ATENCION: %s', ' | '.join(errors))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Pedido ajustado') if not errors else _('Pedido ajustado con observaciones'),
                'message': msg,
                'type': 'warning' if errors else 'success',
                'sticky': bool(errors),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def _added_invoice_is_fiscal(self):
        """Diario con el que el pedido facturaria hoy (lo define
        `_prepare_invoice`: tipo de pedido / diario por defecto)."""
        self.ensure_one()
        try:
            journal_id = self.order_id._prepare_invoice().get('journal_id')
        except UserError:
            return False
        journal = self.env['account.journal'].browse(journal_id)
        return self._journal_is_fiscal(journal)

    @api.model
    def _journal_is_fiscal(self, journal):
        return bool(journal and 'l10n_latam_use_documents' in journal._fields
                    and journal.l10n_latam_use_documents)

    def _check_plan(self):
        precision = self._uom_precision()
        if self.credit_note_mode == 'none' and any(self.line_ids.mapped('combo_dissolve')):
            raise UserError(_(
                'Se desarma un combo: hace falta la nota de credito de la cabecera para poder '
                're-tasar y facturar los componentes. Elegi "Emitir y confirmar" o "Dejar en borrador".'
            ))
        for wl in self.line_ids:
            name = wl.sale_line_id.product_id.display_name
            if float_compare(wl.new_qty, 0, precision_digits=precision) < 0:
                raise UserError(_('La nueva cantidad de "%s" no puede ser negativa.', name))
            if wl.kind != 'combo_parent' and float_compare(wl.new_qty, wl.ordered_qty, precision_digits=precision) > 0:
                raise UserError(_(
                    'La nueva cantidad de "%s" (%s) supera lo pedido (%s). Para agregar, '
                    'cerra esta ventana, subi la cantidad (o agrega el producto) en las '
                    'lineas del pedido y volve a apretar "Ajustar pedido": se genera el '
                    'despacho adicional y la factura por lo agregado.',
                    name, wl.new_qty, wl.ordered_qty,
                ))
            if wl.locked and wl.kind != 'combo_parent' and float_compare(wl.new_qty, wl.ordered_qty, precision_digits=precision) != 0:
                raise UserError(_('La linea "%s" no se puede ajustar desde aqui.', name))
            self._check_swap(wl, name, precision)

    def _check_swap(self, wl, name, precision):
        """Validaciones del canje de embalaje de una linea."""
        if float_compare(wl.swap_qty, 0, precision_digits=precision) < 0:
            raise UserError(_('La cantidad que se lleva de "%s" no puede ser negativa.', name))
        if not wl.swap_qty:
            return
        if not wl.swap_uom_id:
            raise UserError(_('Elegi el embalaje que el cliente se lleva de "%s".', name))
        if wl.locked:
            raise UserError(_('La linea "%s" no admite cambio de embalaje desde aqui.', name))
        product = wl.sale_line_id.product_id
        if wl.swap_uom_id not in (product.uom_id | product.uom_ids):
            raise UserError(_(
                '"%s" no se vende en %s. Elegi uno de los embalajes del producto.',
                name, wl.swap_uom_id.name))
        # No se puede llevar mas de lo que devuelve: eso seria una venta nueva,
        # no un canje. Se compara en la unidad base del producto para poder
        # mezclar embalajes distintos.
        base = product.uom_id
        devuelve = wl.sale_line_id.product_uom_id._compute_quantity(
            max(wl.ordered_qty - wl.new_qty, 0.0), base)
        lleva = wl.swap_uom_id._compute_quantity(wl.swap_qty, base)
        if float_compare(lleva, devuelve, precision_digits=precision) > 0:
            raise UserError(_(
                'En "%s" el cliente se lleva mas de lo que devuelve (%s vs %s %s). '
                'Baja mas la "Nueva cantidad", o agrega el producto en las lineas '
                'del pedido si es una venta adicional.',
                name, wl._fmt(lleva), wl._fmt(devuelve), base.name or ''))

    # --- 1. devoluciones -------------------------------------------------
    def _do_returns(self, plan):
        precision = self._uom_precision()
        order = self.order_id
        allocs = {}  # picking -> {move: qty en UoM del move}
        for wl in plan.filtered(lambda l: l.return_qty > 0):
            sl = wl.sale_line_id
            remaining = wl.return_qty
            outgoing, _incoming = sl._get_outgoing_incoming_moves(strict=False)
            done_out = outgoing.filtered(lambda m: m.state == 'done' and m.picking_id).sorted(
                key=lambda m: (m.date, m.id), reverse=True)
            for move in done_out:
                if float_compare(remaining, 0, precision_digits=precision) <= 0:
                    break
                already = 0.0
                for ret in move.returned_move_ids.filtered(lambda r: r.state != 'cancel'):
                    q = ret.quantity if ret.state == 'done' else ret.product_uom_qty
                    already += ret.product_uom._compute_quantity(q, move.product_uom)
                avail_move = move.quantity - already
                if float_compare(avail_move, 0, precision_digits=precision) <= 0:
                    continue
                avail_line = move.product_uom._compute_quantity(avail_move, sl.product_uom_id)
                take_line = min(remaining, avail_line)
                take_move = sl.product_uom_id._compute_quantity(take_line, move.product_uom)
                allocs.setdefault(move.picking_id, {})
                allocs[move.picking_id][move] = allocs[move.picking_id].get(move, 0.0) + take_move
                remaining -= take_line
            if float_compare(remaining, 0, precision_digits=precision) > 0:
                raise UserError(_(
                    'No hay entregas validadas suficientes para devolver %s %s de "%s" '
                    '(faltan %s). Revisa las devoluciones ya hechas sobre este pedido.',
                    wl.return_qty, sl.product_uom_id.name, sl.product_id.display_name, remaining,
                ))

        pickings = self.env['stock.picking']
        for picking, moves in allocs.items():
            wiz = self.env['stock.return.picking'].with_context(
                active_id=picking.id, active_ids=picking.ids, active_model='stock.picking',
            ).create({'picking_id': picking.id})
            for rl in wiz.product_return_moves:
                qty = moves.get(rl.move_id, 0.0)
                vals = {'quantity': qty}
                if 'to_refund' in rl._fields:
                    vals['to_refund'] = True
                rl.write(vals)
            new_picking = wiz._create_return()
            new_picking.message_post(body=_(
                'Devolucion generada por ajuste del pedido %s. Motivo: %s',
                order.name, self.reason,
            ))
            if self.validate_return:
                self._validate_return_picking(new_picking)
            pickings |= new_picking
        return pickings

    def _validate_return_picking(self, picking):
        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.quantity = move.product_uom_qty
            move.picked = True
        res = picking.with_context(
            skip_backorder=True, skip_sms=True, skip_immediate=True, skip_overprocessed_check=True,
        ).button_validate()
        if res is not True or picking.state != 'done':
            raise UserError(_(
                'No se pudo validar automaticamente la devolucion %s (estado %s). '
                'Desmarca "Validar la devolucion ahora" y validala desde Inventario.',
                picking.name, picking.state,
            ))

    # --- 2. cantidades ---------------------------------------------------
    def _do_quantities(self, plan):
        precision = self._uom_precision()
        for wl in plan:
            sl = wl.sale_line_id
            vals = {}
            if float_compare(wl.target_qty, sl.product_uom_qty, precision_digits=precision) != 0:
                vals['product_uom_qty'] = wl.target_qty
            if wl.release_from_combo and 'surtido_parent_line_id' in sl._fields:
                vals['surtido_parent_line_id'] = False
            if not vals:
                continue
            ctx = {'skip_surtido_detection': True}
            # qty_delivered ya bajo si la devolucion se valido; si quedo
            # pendiente, la coherencia la da la devolucion (ver
            # sale_order_line._update_line_quantity).
            if 'product_uom_qty' in vals and float_compare(
                    wl.target_qty, sl.qty_delivered, precision_digits=precision) < 0:
                ctx['trixo_adjust_skip_delivered_check'] = True
            # `discount` es un campo computado que depende de `product_uom_qty`
            # (core sale_order_line._compute_discount): al bajar la cantidad se
            # recalcula desde la lista de precios -que no da descuento- y se
            # pierde el descuento comercial cargado a mano. No se lo reescribe
            # despues (eso lo volveria a validar contra el tope del usuario que
            # esta ajustando, y no es un descuento nuevo): se protege el campo
            # para que el cambio de cantidad no lo recalcule.
            with self.env.protecting([sl._fields['discount']], sl):
                sl.with_context(**ctx).write(vals)

    # --- 3. notas de credito --------------------------------------------
    def _do_credit_notes(self, plan):
        refunds = self.env['account.move']
        errors = []
        if self.credit_note_mode == 'none':
            return refunds, errors
        precision = self._uom_precision()
        order = self.order_id
        # invoice -> {sale_line: qty a acreditar (en UoM de la linea de venta)}
        per_invoice = {}
        for wl in plan.filtered(lambda l: l.credit_qty > 0):
            sl = wl.sale_line_id
            remaining = wl.credit_qty
            inv_lines = sl.invoice_lines.filtered(
                lambda l: l.move_id.move_type == 'out_invoice' and l.move_id.state == 'posted'
            ).sorted(key=lambda l: (l.move_id.invoice_date or fields.Date.today(), l.move_id.id), reverse=True)
            for il in inv_lines:
                if float_compare(remaining, 0, precision_digits=precision) <= 0:
                    break
                invoiced_here = il.product_uom_id._compute_quantity(il.quantity, sl.product_uom_id)
                already = 0.0
                for rl in sl.invoice_lines.filtered(
                        lambda l: l.move_id.move_type == 'out_refund' and l.move_id.state != 'cancel'
                        and l.move_id.reversed_entry_id == il.move_id and l.product_id == il.product_id):
                    already += rl.product_uom_id._compute_quantity(rl.quantity, sl.product_uom_id)
                avail = invoiced_here - already
                if float_compare(avail, 0, precision_digits=precision) <= 0:
                    continue
                take = min(remaining, avail)
                per_invoice.setdefault(il.move_id, {})
                per_invoice[il.move_id][sl] = per_invoice[il.move_id].get(sl, 0.0) + take
                remaining -= take
            if float_compare(remaining, 0, precision_digits=precision) > 0:
                raise UserError(_(
                    'No se encontro factura confirmada suficiente para acreditar %s %s de "%s" '
                    '(faltan %s).', wl.credit_qty, sl.product_uom_id.name,
                    sl.product_id.display_name, remaining,
                ))

        for invoice, credit_map in per_invoice.items():
            reversal = self.env['account.move.reversal'].with_context(
                active_model='account.move', active_ids=invoice.ids,
            ).create({
                'move_ids': [(6, 0, invoice.ids)],
                'journal_id': invoice.journal_id.id,
                'reason': _('Ajuste %s: %s', order.name, self.reason),
                'date': fields.Date.context_today(self),
            })
            reversal.reverse_moves()
            refund = reversal.new_move_ids
            if len(refund) != 1:
                raise UserError(_('La reversion de %s no devolvio una unica nota de credito.', invoice.name))
            self._trim_refund_lines(refund, credit_map)
            refunds |= refund
            if self.credit_note_mode == 'post':
                err = self._try_post(refund)
                if err:
                    errors.append(_('La NC %s quedo en borrador: %s', refund.display_name, err))
        return refunds, errors

    def _trim_refund_lines(self, refund, credit_map):
        """Deja en la NC (borrador, copia completa de la factura) solo las
        lineas que se acreditan, con la cantidad exacta."""
        precision = self._uom_precision()
        seen = self.env['sale.order.line']
        for rl in refund.invoice_line_ids:
            sls = rl.sale_line_ids & self.env['sale.order.line'].concat(*credit_map.keys())
            sl = sls[:1]
            if not sl or sl in seen:
                rl.unlink()
                continue
            qty = sl.product_uom_id._compute_quantity(credit_map[sl], rl.product_uom_id)
            if float_compare(qty, 0, precision_digits=precision) <= 0:
                rl.unlink()
                continue
            rl.write({'quantity': qty})
            seen |= sl
        # Cualquier linea de seccion/nota u otra sin venta asociada
        refund.line_ids.filtered(lambda l: l.display_type in ('line_section', 'line_note')).unlink()
        if not refund.invoice_line_ids:
            raise UserError(_('La nota de credito de %s quedo sin lineas.', refund.reversed_entry_id.name))
        missing = self.env['sale.order.line'].concat(*credit_map.keys()) - seen
        if missing:
            raise UserError(_(
                'No se pudo ubicar en la factura %s la linea de "%s" para acreditar.',
                refund.reversed_entry_id.name, ', '.join(missing.mapped('product_id.display_name')),
            ))

    def _try_post(self, move):
        """Confirma dentro de un savepoint. Si falla (tipicamente ARCA), el
        documento queda en borrador y devolvemos el mensaje."""
        try:
            with self.env.cr.savepoint():
                move.action_post()
        except Exception as e:  # noqa: BLE001 - acotado al savepoint de un documento
            _logger.warning('trixo_sale_adjust: no se pudo confirmar %s: %s', move.display_name, e, exc_info=True)
            return str(e.args[0]) if e.args else str(e)
        return ''

    # --- 3bis. canje de embalaje ---------------------------------------------
    def _do_swaps(self, plan):
        """Lineas nuevas por lo que el cliente se lleva en otro embalaje.

        El precio lo pone la lista vigente para ese embalaje: si el producto
        tiene recargo por unidad suelta, `sale_packaging_pricing` lo aplica
        solo al calcularse `price_unit`. El descuento se hereda de la linea de
        origen (decision de Tito, 21-09-2026) y se valida como cualquier otro:
        si hay un tope de descuento por usuario, aplica igual que cuando la
        linea se carga a mano en el pedido.

        El despacho de lo que se lleva lo genera el core al crear la linea.
        """
        order = self.order_id
        created = self.env['sale.order.line']
        for wl in plan.filtered(lambda l: l.swap_qty > 0 and l.swap_uom_id):
            sl = wl.sale_line_id
            vals = {
                'order_id': order.id,
                'product_id': sl.product_id.id,
                'product_uom_id': wl.swap_uom_id.id,
                'product_uom_qty': wl.swap_qty,
                'sequence': sl.sequence,
            }
            if sl.discount:
                vals['discount'] = sl.discount
            try:
                new = self.env['sale.order.line'].with_context(
                    skip_surtido_detection=True,
                ).create(vals)
            except (UserError, ValidationError) as e:
                raise UserError(_(
                    'No se pudo agregar "%s" en %s: %s\n\n'
                    'La linea nueva hereda el descuento de la linea de origen '
                    '(%s%%). Si el bloqueo es por el tope de descuento, el ajuste '
                    'lo tiene que hacer un usuario autorizado.',
                    sl.product_id.display_name, wl.swap_uom_id.name,
                    e.args[0] if e.args else str(e), '%.2f' % sl.discount,
                )) from e
            created |= new
        return created

    # --- 4. facturas: combos desarmados (re-tasados) + lo agregado -----------
    def _do_reinvoice(self, plan, extra_lines=None):
        invoices = self.env['account.move']
        errors = []
        order = self.order_id
        children = self._retasar_combo_children(plan)
        added = plan.filtered(
            lambda l: l.invoice_qty > 0 and not l.release_from_combo
        ).mapped('sale_line_id')
        swapped = extra_lines or self.env['sale.order.line']
        to_invoice = (children | added | swapped).filtered(lambda l: l.qty_to_invoice > 0)
        if not to_invoice:
            return invoices, errors
        has_combo = bool(children & to_invoice)
        has_swap = bool(swapped & to_invoice)
        invoices = order.with_context(
            trixo_adjust_only_line_ids=to_invoice.ids, skip_surtido_detection=True,
        )._create_invoices()
        for inv in invoices:
            inv.message_post(body=_(
                'Factura generada por ajuste del pedido %s (%s). Motivo: %s',
                order.name,
                _('combo desarmado') if has_combo
                else (_('cambio de embalaje') if has_swap
                      else _('productos/cantidades agregadas')),
                self.reason,
            ))
            if self._journal_is_fiscal(inv.journal_id):
                # Decision de Tito (17-09-2026): una factura fiscal no se
                # confirma sola; queda en borrador y se avisa.
                errors.append(_(
                    'La factura %s sale por el diario fiscal "%s": quedo en BORRADOR. '
                    'Revisala y confirmala para pedir el CAE.',
                    inv.display_name, inv.journal_id.display_name))
                continue
            if has_combo and self.credit_note_mode != 'post':
                # La NC de la cabecera del combo no esta confirmada: la
                # factura de los componentes la acompania en borrador.
                errors.append(_('La factura %s quedo en borrador junto con la nota de credito.',
                                inv.display_name))
                continue
            err = self._try_post(inv)
            if err:
                errors.append(_('La factura %s quedo en borrador: %s', inv.display_name, err))
        return invoices, errors

    def _retasar_combo_children(self, plan):
        """Componentes liberados de un combo desarmado: precio y descuento a
        la lista vigente. Devuelve las lineas a facturar."""
        children = plan.filtered(lambda l: l.release_from_combo).mapped('sale_line_id')
        if not children:
            return children
        order = self.order_id
        # qty_invoiced ya bajo a 0 por la NC (los borradores cuentan), asi que
        # el core acepta recomputar el precio desde la lista vigente.
        children = children.with_context(skip_surtido_detection=True)
        children.with_context(force_price_recomputation=True)._compute_price_unit()
        children._compute_discount()
        zero = children.filtered(lambda l: l.product_uom_qty > 0 and float_is_zero(
            l.price_unit, precision_rounding=l.currency_id.rounding))
        if zero:
            raise UserError(_(
                'Al desarmar el combo, estos productos quedaron con precio 0 en la lista '
                '"%s": %s. Revisa la lista de precios antes de ajustar.',
                order.pricelist_id.display_name, ', '.join(zero.mapped('product_id.display_name')),
            ))
        if self.credit_note_mode == 'none':
            return children.browse()
        return children

    # --- 5. conciliacion ---------------------------------------------------
    def _do_reconcile(self, refunds, invoices):
        posted_refunds = refunds.filtered(lambda m: m.state == 'posted')
        if not posted_refunds:
            return
        order = self.order_id
        candidates = (invoices | order.invoice_ids).filtered(
            lambda m: m.state == 'posted' and m.move_type == 'out_invoice'
            and m.payment_state in ('not_paid', 'partial')
        ).sorted(key=lambda m: (m not in invoices, m.invoice_date or fields.Date.today(), m.id))
        for refund in posted_refunds:
            for inv in candidates:
                if refund.payment_state in ('paid', 'in_payment', 'reversed'):
                    break
                if inv.payment_state not in ('not_paid', 'partial'):
                    continue
                lines = (refund.line_ids + inv.line_ids).filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
                )
                if len(lines.mapped('account_id')) != 1 or len(lines.mapped('partner_id')) > 1:
                    continue
                lines.reconcile()

    # --- 6. chatter ----------------------------------------------------------
    def _post_messages(self, plan, returns, refunds, invoices, errors):
        order = self.order_id
        rows = Markup('')
        for wl in plan:
            rows += Markup('<li><b>%s</b>: %s &rarr; %s %s &mdash; %s</li>') % (
                wl.sale_line_id.product_id.display_name, wl._fmt(wl.ordered_qty),
                wl._fmt(wl.target_qty), wl.sale_line_id.product_uom_id.name or '',
                wl.action_summary or '',
            )
        body = Markup('<p><b>%s</b> (%s). %s: %s</p><ul>%s</ul>') % (
            _('Ajuste de pedido'), self.env.user.name, _('Motivo'), self.reason, rows)
        for rec, label in ((returns, _('Devoluciones')), (refunds, _('Notas de credito')),
                           (invoices, _('Facturas'))):
            if rec:
                links = Markup(', ').join(
                    Markup('<a href="#" data-oe-model="%s" data-oe-id="%s">%s</a>') % (
                        r._name, r.id, r.display_name) for r in rec)
                body += Markup('<p>%s: %s</p>') % (label, links)
        if errors:
            body += Markup('<p><b>%s:</b> %s</p>') % (_('Observaciones'), ' | '.join(errors))
        order.message_post(body=body)


class SaleOrderAdjustLine(models.TransientModel):
    _name = 'sale.order.adjust.line'
    _description = 'Linea de ajuste de pedido'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('sale.order.adjust', required=True, ondelete='cascade')
    sale_line_id = fields.Many2one('sale.order.line', string='Linea', required=True, readonly=True)
    sequence = fields.Integer(readonly=True)
    product_id = fields.Many2one(related='sale_line_id.product_id')
    uom_id = fields.Many2one(related='sale_line_id.product_uom_id', string='UdM')
    price_unit = fields.Float(related='sale_line_id.price_unit')
    kind = fields.Selection([
        ('normal', 'Linea'),
        ('combo_parent', 'Cabecera de combo'),
        ('combo_child', 'Componente de combo'),
    ], readonly=True)
    combo_parent_line_id = fields.Many2one('sale.order.line', readonly=True)
    locked = fields.Boolean(readonly=True)

    ordered_qty = fields.Float(string='Pedido', digits='Product Unit', readonly=True)
    delivered_qty = fields.Float(string='Entregado', digits='Product Unit', readonly=True)
    invoiced_qty = fields.Float(string='Facturado', digits='Product Unit', readonly=True)
    new_qty = fields.Float(string='Nueva cantidad', digits='Product Unit')

    # Canje de embalaje (19.0.1.3.0): lo que el cliente se lleva A CAMBIO de lo
    # que devuelve, en otro embalaje del mismo producto. No se toca la linea
    # original (una linea no puede estar en dos embalajes): se factura aparte.
    allowed_uom_ids = fields.Many2many(
        'uom.uom', string='Embalajes del producto',
        compute='_compute_allowed_uom_ids')
    swap_qty = fields.Float(
        string='Se lleva', digits='Product Unit',
        help='Cantidad que el cliente se lleva EN OTRO EMBALAJE a cambio de lo '
             'que devuelve. Se factura aparte, al precio de la lista vigente '
             'para ese embalaje (si el producto tiene recargo por suelto, se '
             'aplica solo) y con el descuento de la linea de origen.')
    swap_uom_id = fields.Many2one(
        'uom.uom', string='En embalaje',
        domain="[('id', 'in', allowed_uom_ids)]")

    # plan
    target_qty = fields.Float(digits='Product Unit', readonly=True)
    return_qty = fields.Float(string='Devolver', digits='Product Unit', readonly=True)
    cancel_qty = fields.Float(string='Cancelar', digits='Product Unit', readonly=True)
    credit_qty = fields.Float(string='NC', digits='Product Unit', readonly=True)
    reinvoice_qty = fields.Float(digits='Product Unit', readonly=True)
    pending_invoice_qty = fields.Float(digits='Product Unit', readonly=True)
    invoice_qty = fields.Float(string='Facturar', digits='Product Unit', readonly=True)
    combo_dissolve = fields.Boolean(readonly=True)
    release_from_combo = fields.Boolean(readonly=True)
    has_action = fields.Boolean(readonly=True)
    action_summary = fields.Char(string='Que va a pasar', readonly=True)

    @api.depends('sale_line_id')
    def _compute_allowed_uom_ids(self):
        # Mismo criterio que el core (sale_order_line._compute_allowed_uom_ids):
        # `product.uom_ids` son los embalajes ADICIONALES y NO incluye la unidad
        # base del producto, que es justamente la que el cliente se lleva cuando
        # devuelve un bulto y se lleva 2 unidades sueltas.
        for wl in self:
            product = wl.sale_line_id.product_id
            wl.allowed_uom_ids = product.uom_id | product.uom_ids

    def _fmt(self, qty):
        precision = self.wizard_id._uom_precision()
        qty = float_round(qty, precision_digits=precision)
        return ('%g' % qty) if qty == int(qty) else ('%.*f' % (precision, qty))

    def _build_action_summary(self):
        self.ensure_one()
        uom = self.uom_id.name or ''
        parts = []
        if self.kind == 'combo_parent':
            if self.combo_dissolve:
                parts.append(_('Combo se desarma: NC por %s x %s', self._fmt(self.credit_qty), uom))
                if self.return_qty:
                    parts.append(_('devolucion %s', self._fmt(self.return_qty)))
                return ' · '.join(parts)
            return _('Combo se mantiene')
        if self.cancel_qty:
            parts.append(_('cancela pendiente %s %s', self._fmt(self.cancel_qty), uom))
        if self.return_qty:
            parts.append(_('devolucion %s %s', self._fmt(self.return_qty), uom))
        if self.release_from_combo:
            parts.append(_('sale del combo: NC de %s a $0 y factura %s a precio de lista',
                           self._fmt(self.credit_qty), self._fmt(self.reinvoice_qty)))
        elif self.credit_qty:
            parts.append(_('NC por %s %s', self._fmt(self.credit_qty), uom))
        if self.invoice_qty:
            parts.append(_('factura por %s %s (agregado)', self._fmt(self.invoice_qty), uom))
        if self.swap_qty and self.swap_uom_id:
            parts.append(_('se lleva %s %s a cambio (se factura aparte a precio de lista)',
                           self._fmt(self.swap_qty), self.swap_uom_id.name))
        return ' · '.join(parts) if parts else _('Sin cambios')
