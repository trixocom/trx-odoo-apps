# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom
# License OPL-1 (see LICENSE file at repository root).
from odoo import api, fields, models


class TrxCobranzaDashboard(models.AbstractModel):
    _name = 'trx.cobranza.dashboard'
    _description = "Panel de control de cobranzas"

    @api.model
    def get_data(self):
        """Datos del tablero. Un solo round-trip para toda la pantalla."""
        Move = self.env['account.move']
        hoy = fields.Date.context_today(self)
        mes0 = hoy.replace(day=1)
        base = [
            ('move_type', '=', 'out_invoice'),
            ('is_subscription_invoice', '=', True),
            ('state', '=', 'posted'),
        ]
        todas = Move.search(base)
        fact_mes = todas.filtered(
            lambda m: m.invoice_date and m.invoice_date >= mes0)
        cobradas = todas.filtered(
            lambda m: m.payment_state in ('paid', 'in_payment'))
        pendientes = todas.filtered(
            lambda m: m.payment_state in ('not_paid', 'partial'))
        vencidas = pendientes.filtered(
            lambda m: m.invoice_date_due and m.invoice_date_due < hoy)

        total_fact = sum(todas.mapped('amount_total'))
        total_cobrado = sum(cobradas.mapped('amount_total'))
        efectividad = total_fact and round(
            100.0 * total_cobrado / total_fact, 1) or 0.0

        # ---------------- Rechazos (SIRO + PAGOS360) ----------------
        rechazos = []
        Rend = self.env['siro.rendicion'].sudo()
        BatchLine = self.env['siro.debt.batch.line'].sudo()
        for r in Rend.search([('is_rejection', '=', True)],
                             order='fecha_proceso desc, id desc', limit=80):
            line = BatchLine.search([
                ('cpe', '=', r.cpe),
                ('nro_comprobante', '=', r.nro_comprobante),
            ], limit=1)
            rechazos.append({
                'id': r.id,
                'model': 'siro.rendicion',
                'fecha': str(r.fecha_proceso or ''),
                'cliente': line.partner_id.display_name or r.cpe or '?',
                'comprobante': line.move_id.name or r.nro_comprobante or '',
                'importe': line.importe_vto_1 or r.importe or 0.0,
                'motivo': (r.motivo_cliente or r.descripcion_rechazo
                           or r.codigo_rechazo or 'Motivo no informado'),
                'codigo': r.codigo_rechazo or '',
                'canal': 'SIRO',
            })
        if 'pagos360.debit.request' in self.env:
            Deb = self.env['pagos360.debit.request'].sudo()
            for d in Deb.search([('state', 'in', ('rejected', 'expired'))],
                                order='id desc', limit=80):
                rechazos.append({
                    'id': d.id,
                    'model': 'pagos360.debit.request',
                    'fecha': str(d.first_due_date or ''),
                    'cliente': d.partner_id.display_name or '?',
                    'comprobante': d.move_id.name or '',
                    'importe': d.amount or 0.0,
                    'motivo': ("Débito vencido sin cobrar"
                               if d.state == 'expired'
                               else "Débito rechazado"),
                    'codigo': d.pagos360_debit_id or '',
                    'canal': 'PAGOS360',
                })
        rechazos.sort(key=lambda x: x['fecha'], reverse=True)
        total_rechazado = sum(x['importe'] for x in rechazos)

        # ---------------- Pendientes ----------------
        pend_rows = [{
            'id': m.id,
            'model': 'account.move',
            'comprobante': m.name,
            'cliente': m.partner_id.display_name,
            'importe': m.amount_total,
            'vencimiento': str(m.invoice_date_due or ''),
            'vencida': bool(m.invoice_date_due and m.invoice_date_due < hoy),
            'en_base': bool(m.siro_debt_batch_line_id),
        } for m in pendientes.sorted(
            key=lambda m: m.invoice_date_due or hoy)[:80]]

        # ---------------- Adhesiones ----------------
        adh_siro = self.env['payment.token'].sudo().search_count([
            ('provider_id.code', '=', 'siro_roela'), ('active', '=', True)])
        adh_p360 = 0
        if 'pagos360.adhesion' in self.env:
            adh_p360 = self.env['pagos360.adhesion'].sudo().search_count(
                [('state', '=', 'signed')])

        moneda = self.env.company.currency_id
        return {
            'fecha': str(hoy),
            'moneda': moneda.symbol or '$',
            'kpis': {
                'facturado_mes': sum(fact_mes.mapped('amount_total')),
                'facturado_mes_qty': len(fact_mes),
                'cobrado': total_cobrado,
                'cobrado_qty': len(cobradas),
                'pendiente': sum(pendientes.mapped('amount_residual')),
                'pendiente_qty': len(pendientes),
                'vencido': sum(vencidas.mapped('amount_residual')),
                'vencido_qty': len(vencidas),
                'rechazado': total_rechazado,
                'rechazado_qty': len(rechazos),
                'efectividad': efectividad,
                'suscripciones_activas': self.env['sale.order'].search_count([
                    ('is_subscription', '=', True),
                    ('subscription_state', '=', '2_progress')]),
                'adhesiones': adh_siro + adh_p360,
                'adh_siro': adh_siro,
                'adh_p360': adh_p360,
            },
            'rechazos': rechazos[:40],
            'pendientes': pend_rows,
        }
