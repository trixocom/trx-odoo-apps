# -*- coding: utf-8 -*-
"""Wizard "Ajustar pedido": una sola pantalla para cancelar pendientes,
devolver mercaderia entregada y emitir la nota de credito que corresponda
sobre un pedido confirmado, incluso facturado y cobrado.

Orden de ejecucion (una transaccion):
  1. devoluciones (stock.return.picking core, to_refund=True)
  2. baja de cantidades (el core cancela los movimientos pendientes)
  3. notas de credito (reversion parcial de la factura original via el
     wizard estandar account.move.reversal)
  3bis. lineas nuevas: lo que el cliente se lleva ("Se lleva", mismo
     producto en cualquier embalaje) y los productos agregados ("Agregar
     productos"). Precio y descuento salen de las reglas vigentes (lista de
     precios, recargo por embalaje); el despacho lo genera el core.
  4. facturas: componentes de combos desarmados (re-tasados), lineas
     nuevas y cualquier pendiente de facturar. Si el pedido ya tenia
     facturas se factura SIEMPRE, con el diario de la factura de origen.
     Diario no fiscal: se confirma en el acto. Diario fiscal
     (l10n_latam_use_documents): queda en borrador y se avisa.
  5. conciliacion NC <-> facturas impagas de la orden

19.0.1.5.0: en un pedido confirmado las lineas ya no se editan desde el
formulario (ver sale_order.write): todo cambio pasa por este wizard.
19.0.1.5.1: el congelamiento rige desde que el pedido tiene una factura de
cliente vigente; antes se editan como siempre.
"""
import logging
from collections import defaultdict

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
    # 19.0.1.5.0: ya no es una opcion del usuario. Vale True cuando el pedido
    # ya tiene facturas: entonces todo lo que se agrega o se lleva se factura
    # en el acto. En un pedido que nunca se facturo, lo agregado queda
    # pendiente y se factura con el resto por el circuito normal.
    invoice_added = fields.Boolean(string='Facturar lo agregado', readonly=True)
    prefill_notice = fields.Char(readonly=True)
    line_ids = fields.One2many('sale.order.adjust.line', 'wizard_id', string='Lineas')
    add_line_ids = fields.One2many('sale.order.adjust.add', 'wizard_id',
                                   string='Agregar productos')
    summary_html = fields.Html(string='Resumen', compute='_compute_summary', sanitize=False)
    has_changes = fields.Boolean(compute='_compute_summary')
    has_credit = fields.Boolean(compute='_compute_summary')
    has_return = fields.Boolean(compute='_compute_summary')
    has_invoice = fields.Boolean(compute='_compute_summary')
    has_pending_invoice = fields.Boolean(compute='_compute_summary')
    invoice_is_fiscal = fields.Boolean(compute='_compute_summary')
    combo_warning = fields.Char(compute='_compute_summary')

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
                # Pedido ya facturado: lo que se agrega se factura siempre.
                # Pedido nunca facturado: sigue el circuito normal.
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
            # Muchas columnas (cantidades, canje de embalaje y el detalle de
            # que va a pasar): con el ancho por defecto se cortan.
            'context': {'dialog_size': 'extra-large'},
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
                'returned_qty': 0.0,
                'locked': kind == 'combo_parent' or sl.is_downpayment,
            })
        Line.create(vals_list)
        self._compute_lines_from_new_qty()

    def _apply_requested_quantities(self, requested):
        """Carga en "Devuelve" lo que el usuario bajo en las lineas del
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
            wl.returned_qty = max(wl.ordered_qty - qty, 0.0)
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
            wl.returned_qty = max(
                wl.ordered_qty - min(wl.ordered_qty, wl.delivered_qty), 0.0)
        self._compute_lines_from_new_qty()
        return self._get_action()

    # ------------------------------------------------------------------
    # Plan (preview) — se recalcula con cada cambio de "Devuelve"
    # ------------------------------------------------------------------
    @api.onchange('line_ids', 'add_line_ids')
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

            # 19.0.1.4.0: el usuario carga lo que el cliente DEVUELVE. La
            # cantidad que queda en la linea es una cuenta, y hacersela hacer
            # al de mostrador era pedir un error. El resto del wizard sigue
            # razonando sobre `new_qty`, que ahora se deriva aca.
            #
            # 19.0.1.5.0: "Se lleva" en el MISMO embalaje de la linea se
            # compensa con lo que devuelve (devuelve 1 bulto y se lleva 3 ->
            # se factura 2, sin NC); en otro embalaje no hay nada que compensar.
            for wl in lines:
                ret = max(wl.returned_qty, 0.0)
                wl.swap_create_qty = max(wl.swap_qty, 0.0) if wl.swap_uom_id else 0.0
                if wl.swap_create_qty and wl.swap_uom_id == wl.sale_line_id.product_uom_id:
                    net = min(ret, wl.swap_create_qty)
                    ret -= net
                    wl.swap_create_qty -= net
                wl.new_qty = max(wl.ordered_qty - ret, 0.0)

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
                    or cmp(wl.invoice_qty, 0) > 0 or cmp(wl.swap_create_qty, 0) > 0
                    or wl.release_from_combo or cmp(wl.target_qty, ordered) != 0
                )
                wl.action_summary = wl._build_action_summary()
            for al in wizard.add_line_ids:
                al.action_summary = al._build_action_summary()

    @api.depends('line_ids.returned_qty', 'line_ids.swap_qty', 'line_ids.swap_uom_id',
                 'line_ids.action_summary', 'add_line_ids.product_id', 'add_line_ids.qty',
                 'add_line_ids.uom_id', 'credit_note_mode', 'validate_return', 'invoice_added')
    def _compute_summary(self):
        for wizard in self:
            lines = wizard.line_ids.filtered('has_action')
            adds = wizard._valid_add_lines()
            wizard.has_changes = bool(lines or adds)
            wizard.has_return = any(l.return_qty > 0 for l in lines)
            wizard.has_credit = any(l.credit_qty > 0 for l in lines)
            wizard.has_invoice = any(l.invoice_qty > 0 for l in lines)
            wizard.has_pending_invoice = any(
                l.pending_invoice_qty > 0 for l in wizard.line_ids)
            wizard.invoice_is_fiscal = wizard._added_invoice_is_fiscal()
            wizard.combo_warning = wizard._combo_warning() or False
            if not lines and not adds:
                wizard.summary_html = _('<i>Sin cambios: carga en "Devuelve" lo que el cliente devuelve, en "Se lleva" lo que se lleva del mismo producto (en cualquier embalaje) y en "Agregar productos" lo que se suma al pedido.</i>')
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
            n_new = sum(1 for l in lines if l.swap_create_qty > 0) + len(adds)
            if n_new:
                parts.append(_('%s linea(s) nueva(s) en el pedido por lo que el cliente se lleva, '
                               'al precio vigente', n_new))
            n_inv = sum(1 for l in lines if l.invoice_qty > 0)
            if (n_new or n_inv) and wizard.invoice_added:
                parts.append(_('se factura con el diario de la factura de origen%s',
                               _(' — diario fiscal: queda en BORRADOR para revisar y confirmar')
                               if wizard.invoice_is_fiscal else _(' — se confirma ahora')))
            elif n_new:
                parts.append(_('el pedido todavia no se facturo: lo agregado queda pendiente '
                               'y se factura con el resto'))
            if wizard.combo_warning:
                parts.append(wizard.combo_warning)
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
        adds = self._valid_add_lines()
        if not plan and not adds:
            raise UserError(_('No hay cambios para aplicar.'))

        ctx_lines = plan.with_context(skip_surtido_detection=True)
        returns = self._do_returns(ctx_lines)
        self._do_quantities(ctx_lines)
        refunds, refund_errors = self._do_credit_notes(ctx_lines)
        new_lines = self._do_additions(ctx_lines, adds)
        invoices, invoice_errors = self._do_reinvoice(ctx_lines, new_lines=new_lines)
        self._do_reconcile(refunds, invoices)
        self._post_messages(plan, returns, refunds, invoices, refund_errors + invoice_errors,
                            new_lines=new_lines)

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
        """True si algo de lo que se va a facturar en el ajuste sale por un
        diario fiscal (el de la factura de origen de cada linea)."""
        self.ensure_one()
        if not self.invoice_added:
            return False
        journals = self.env['account.journal']
        for wl in self.line_ids:
            if wl.swap_create_qty > 0 or wl.invoice_qty > 0:
                journals |= self._origin_journal(wl.sale_line_id)
        if self._valid_add_lines():
            journals |= self._order_journal()
        return any(self._journal_is_fiscal(j) for j in journals)

    def _posted_invoices(self, moves):
        return moves.filtered(
            lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
        ).sorted(key=lambda m: (m.invoice_date or fields.Date.today(), m.id))

    def _order_journal(self):
        """Diario de la ultima factura del pedido (para productos que no
        estaban en el pedido)."""
        moves = self._posted_invoices(self.order_id.invoice_ids)
        return moves[-1:].journal_id

    def _origin_journal(self, sale_line):
        """Diario de la ultima factura de esa linea; si la linea no se
        facturo, el de la ultima factura del pedido (decision de Tito
        22-09-2026: si devuelve algo de una FA-B, lo que se lleva sale en
        FA-B)."""
        if not sale_line:
            return self._order_journal()
        moves = self._posted_invoices(sale_line.invoice_lines.mapped('move_id'))
        return moves[-1:].journal_id or self._order_journal()

    def _valid_add_lines(self):
        return self.add_line_ids.filtered(lambda a: a.product_id and a.qty > 0)

    def _combo_warning(self):
        """Aviso si con lo que se agrega o se lleva se completaria un combo
        (surtido). El modulo de surtidos no arma combos sobre pedidos
        confirmados -desarma y rearma todo el pedido, lo que reescribiria
        lineas ya facturadas- y el ajuste tampoco: solo avisa (decision de
        Tito 22-09-2026). Nunca rompe el wizard."""
        self.ensure_one()
        order = self.order_id
        if not hasattr(order, '_get_active_surtidos'):
            return ''
        try:
            extra = [(wl.sale_line_id.product_id, wl.swap_uom_id, wl.swap_create_qty)
                     for wl in self.line_ids if wl.swap_create_qty > 0 and wl.swap_uom_id]
            extra += [(a.product_id, a.uom_id, a.qty) for a in self._valid_add_lines()]
            if not extra:
                return ''
            base = [(wl.sale_line_id.product_id, wl.sale_line_id.product_uom_id, wl.new_qty)
                    for wl in self.line_ids if wl.kind == 'normal']
            pkg_name = self.env['ir.config_parameter'].sudo().get_param(
                'stock_packaging_report.packaging_name', default='')

            def bultos(product, uom, qty):
                # Mismo criterio que sale.order._surtido_line_bultos: solo
                # cuenta lo cargado en el embalaje por defecto (bulto).
                if pkg_name:
                    pkg = (product._trixo_default_packaging_uom()
                           if hasattr(product, '_trixo_default_packaging_uom') else False)
                    if not pkg or uom != pkg:
                        return 0.0
                return qty

            names = []
            for surtido in order._get_active_surtidos():
                p2g = order._build_product_to_group_map(surtido)

                def factor(items, surtido=surtido, p2g=p2g):
                    totals = defaultdict(float)
                    for product, uom, qty in items:
                        gid = p2g.get(product.id)
                        if gid:
                            totals[gid] += bultos(product, uom, qty)
                    factors = []
                    for group in surtido.group_ids:
                        if group.required_qty <= 0 or totals[group.id] <= 0:
                            return 0
                        factors.append(int(totals[group.id] // group.required_qty))
                    return min(factors) if factors else 0

                if factor(base + extra) > factor(base):
                    names.append(surtido.display_name)
            if not names:
                return ''
            return _('ATENCION: con lo que se agrega se completaria el combo %s. El ajuste '
                     'no arma combos sobre un pedido confirmado: se factura a precio de lista.',
                     ', '.join(names))
        except Exception:  # noqa: BLE001 - un aviso nunca debe romper el ajuste
            _logger.warning('trixo_sale_adjust: no se pudo evaluar combos', exc_info=True)
            return ''

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
            if float_compare(wl.returned_qty, 0, precision_digits=precision) < 0:
                raise UserError(_('Lo que devuelve de "%s" no puede ser negativo.', name))
            if wl.kind != 'combo_parent' and float_compare(wl.returned_qty, wl.ordered_qty, precision_digits=precision) > 0:
                raise UserError(_(
                    'No se puede devolver %s de "%s": el pedido tiene %s. Si el cliente '
                    'se lleva MAS, cargalo en "Se lleva" (mismo producto) o en "Agregar '
                    'productos".',
                    wl._fmt(wl.returned_qty), name, wl._fmt(wl.ordered_qty),
                ))
            if wl.locked and wl.kind != 'combo_parent' and float_compare(wl.returned_qty, 0, precision_digits=precision) != 0:
                raise UserError(_('La linea "%s" no se puede ajustar desde aqui.', name))
            self._check_swap(wl, name, precision)
        for al in self.add_line_ids:
            if not al.product_id and not al.qty:
                continue
            if not al.product_id:
                raise UserError(_('Elegi el producto a agregar.'))
            name = al.product_id.display_name
            if float_compare(al.qty, 0, precision_digits=precision) <= 0:
                raise UserError(_('Indica cuanto se agrega de "%s".', name))
            if not al.product_id.sale_ok:
                raise UserError(_('"%s" no se puede vender.', name))
            if not al.uom_id or al.uom_id not in (al.product_id.uom_id | al.product_id.uom_ids):
                raise UserError(_('Elegi uno de los embalajes de "%s".', name))

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
        # 19.0.1.5.0: sin tope. "Se lleva" sirve tambien para vender mas del
        # mismo producto; en el mismo embalaje se compensa con lo que devuelve.

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

    # --- 3bis. lineas nuevas: lo que se lleva y lo que se agrega ----------------
    def _do_additions(self, plan, adds):
        """Crea las lineas por lo que el cliente se lleva ("Se lleva", neto de
        la compensacion en el mismo embalaje) y por los productos agregados.

        Precio y descuento salen de las reglas vigentes: lista de precios y,
        si el producto tiene recargo por embalaje, `sale_packaging_pricing`
        lo aplica solo. No se copia el descuento manual de la linea de origen
        (decision de Tito 22-09-2026). El tope de descuento por usuario, si
        lo hubiera, aplica igual que siempre.

        El despacho lo genera el core al crear la linea en un pedido
        confirmado. Devuelve {linea nueva: linea de origen o vacio}."""
        order = self.order_id
        Line = self.env['sale.order.line'].with_context(
            skip_surtido_detection=True, trixo_adjust_allow_line_edit=True,
        )
        created = {}
        for wl in plan.filtered(lambda l: l.swap_create_qty > 0 and l.swap_uom_id):
            sl = wl.sale_line_id
            new = self._create_order_line(
                Line, sl.product_id, wl.swap_uom_id, wl.swap_create_qty, sl.sequence)
            created[new] = sl
        seq = max(order.order_line.mapped('sequence') or [10]) + 1
        for al in adds:
            new = self._create_order_line(Line, al.product_id, al.uom_id, al.qty, seq)
            created[new] = self.env['sale.order.line']
            seq += 1
        return created

    def _create_order_line(self, Line, product, uom, qty, sequence):
        try:
            return Line.create({
                'order_id': self.order_id.id,
                'product_id': product.id,
                'product_uom_id': uom.id,
                'product_uom_qty': qty,
                'sequence': sequence,
            })
        except (UserError, ValidationError) as e:
            raise UserError(_(
                'No se pudo agregar "%s" en %s: %s',
                product.display_name, uom.name, e.args[0] if e.args else str(e),
            )) from e

    # --- 4. facturas: combos desarmados, lineas nuevas y pendientes ----------
    def _do_reinvoice(self, plan, new_lines=None):
        """Factura lo que corresponda, agrupado por diario de origen: cada
        linea sale con el diario de la factura de la que viene (una linea
        nueva de "Se lleva", el de la linea que devuelve; un componente de
        combo desarmado, el de la cabecera; un producto agregado, el de la
        ultima factura del pedido)."""
        invoices = self.env['account.move']
        errors = []
        order = self.order_id
        SOL = self.env['sale.order.line']
        new_lines = new_lines or {}
        # la cabecera se lee del wizard: _do_quantities ya desengancho la linea
        combo_origin = {wl.sale_line_id: wl.combo_parent_line_id
                        for wl in plan if wl.release_from_combo}
        children = self._retasar_combo_children(plan)
        added = plan.filtered(
            lambda l: l.invoice_qty > 0 and not l.release_from_combo
        ).mapped('sale_line_id')
        created = SOL.concat(*new_lines.keys()) if new_lines else SOL
        if not self.invoice_added:
            # Pedido nunca facturado: lo nuevo queda pendiente, con el resto.
            created = SOL
        to_invoice = (children | added | created).filtered(lambda l: l.qty_to_invoice > 0)
        if not to_invoice:
            return invoices, errors

        groups = defaultdict(lambda: SOL)
        for line in to_invoice:
            if line in combo_origin:
                origin = combo_origin[line]
            elif line in new_lines:
                origin = new_lines[line]
            else:
                origin = line
            journal = self._origin_journal(origin)
            groups[journal.id or False] |= line

        for journal_id, lines in groups.items():
            ctx = {'trixo_adjust_only_line_ids': lines.ids, 'skip_surtido_detection': True}
            if journal_id:
                ctx['trixo_adjust_journal_id'] = journal_id
            new_invoices = order.with_context(**ctx)._create_invoices()
            has_combo = bool(lines & children)
            has_new = bool(lines & created)
            for inv in new_invoices:
                inv.message_post(body=_(
                    'Factura generada por ajuste del pedido %s (%s). Motivo: %s',
                    order.name,
                    _('combo desarmado') if has_combo
                    else (_('lo que el cliente se lleva') if has_new
                          else _('productos/cantidades agregadas')),
                    self.reason,
                ))
                if self._journal_is_fiscal(inv.journal_id):
                    # Decision de Tito (17-09 y 22-09-2026): una factura
                    # fiscal no se confirma sola; queda en borrador y se avisa.
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
            invoices |= new_invoices
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
    def _post_messages(self, plan, returns, refunds, invoices, errors, new_lines=None):
        order = self.order_id
        rows = Markup('')
        for wl in plan:
            rows += Markup('<li><b>%s</b>: %s &rarr; %s %s &mdash; %s</li>') % (
                wl.sale_line_id.product_id.display_name, wl._fmt(wl.ordered_qty),
                wl._fmt(wl.target_qty), wl.sale_line_id.product_uom_id.name or '',
                wl.action_summary or '',
            )
        for line, origin in (new_lines or {}).items():
            rows += Markup('<li><b>%s</b>: %s %s %s</li>') % (
                line.product_id.display_name,
                _('se lleva (canje)') if origin else _('se agrega'),
                line.product_uom_qty, line.product_uom_id.name or '',
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
    returned_qty = fields.Float(
        string='Devuelve', digits='Product Unit',
        help='Cantidad que el cliente devuelve o no se lleva, en el embalaje de '
             'la linea. Si a cambio se lleva el mismo producto en otro embalaje, '
             'cargalo en "Se lleva".')
    new_qty = fields.Float(
        string='Queda', digits='Product Unit', readonly=True,
        help='Cantidad que queda en la linea del pedido: lo pedido menos lo que '
             'el cliente devuelve. Se calcula solo.')

    # Canje de embalaje (19.0.1.3.0): lo que el cliente se lleva A CAMBIO de lo
    # que devuelve, en otro embalaje del mismo producto. No se toca la linea
    # original (una linea no puede estar en dos embalajes): se factura aparte.
    allowed_uom_ids = fields.Many2many(
        'uom.uom', string='Embalajes del producto',
        compute='_compute_allowed_uom_ids')
    swap_qty = fields.Float(
        string='Se lleva', digits='Product Unit',
        help='Cantidad que el cliente se lleva del mismo producto, en el embalaje '
             'que elijas en "En embalaje". Se agrega como linea nueva y se factura '
             'al precio vigente (con recargo por embalaje si corresponde). En el '
             'mismo embalaje de la linea se compensa con lo que devuelve.')
    swap_create_qty = fields.Float(digits='Product Unit', readonly=True)
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
            same = self.swap_uom_id == self.sale_line_id.product_uom_id
            if self.swap_create_qty:
                parts.append(_('se lleva %s %s%s, a precio vigente%s',
                               self._fmt(self.swap_create_qty), self.swap_uom_id.name,
                               _(' mas (neto de lo que devuelve)') if same else '',
                               '' if self.wizard_id.invoice_added
                               else _(' (se factura con el pedido)')))
            elif same:
                parts.append(_('se lleva %s %s: se descuenta de lo que devuelve',
                               self._fmt(self.swap_qty), self.swap_uom_id.name))
        return ' · '.join(parts) if parts else _('Sin cambios')


class SaleOrderAdjustAdd(models.TransientModel):
    """Producto que se suma al pedido desde el ajuste (19.0.1.5.0): las
    lineas de un pedido facturado ya no se editan en el formulario."""
    _name = 'sale.order.adjust.add'
    _description = 'Producto agregado en el ajuste de pedido'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('sale.order.adjust', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product', string='Producto',
        domain="[('sale_ok', '=', True)]")
    allowed_uom_ids = fields.Many2many(
        'uom.uom', string='Embalajes del producto',
        compute='_compute_allowed_uom_ids')
    qty = fields.Float(string='Cantidad', digits='Product Unit', default=1.0)
    uom_id = fields.Many2one(
        'uom.uom', string='Embalaje',
        domain="[('id', 'in', allowed_uom_ids)]")
    action_summary = fields.Char(string='Que va a pasar', readonly=True)

    @api.depends('product_id')
    def _compute_allowed_uom_ids(self):
        for al in self:
            al.allowed_uom_ids = al.product_id.uom_id | al.product_id.uom_ids

    @api.onchange('product_id')
    def _onchange_product_id(self):
        product = self.product_id
        if not product:
            self.uom_id = False
            return
        default = (product._trixo_default_packaging_uom()
                   if hasattr(product, '_trixo_default_packaging_uom') else False)
        self.uom_id = default or product.uom_id

    def _build_action_summary(self):
        self.ensure_one()
        if not self.product_id or self.qty <= 0 or not self.uom_id:
            return ''
        qty = self.wizard_id.line_ids[:1]._fmt(self.qty) if self.wizard_id.line_ids else self.qty
        if self.wizard_id.invoice_added:
            return _('se agrega %s %s a precio vigente, se despacha y se factura',
                     qty, self.uom_id.name)
        return _('se agrega %s %s a precio vigente (se factura con el pedido)',
                 qty, self.uom_id.name)
