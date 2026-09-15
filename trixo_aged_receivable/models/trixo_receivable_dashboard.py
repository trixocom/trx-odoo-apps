# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License AGPL-3.0
from datetime import date, timedelta

from odoo import _, api, models
from odoo.tools import SQL

from .trixo_receivable_line import BUCKETS

TOP_N = 10


class TrixoReceivablePartnerDashboard(models.Model):
    """Datos del tablero de Deudores.

    Se cuelgan del modelo del resumen (que ya tiene su ACL) para que el
    cliente OWL los pida con una sola llamada, sin exponer un modelo nuevo.
    """

    _inherit = "trixo.receivable.partner"

    # ------------------------------------------------------------------
    # Saldo a una fecha pasada
    # ------------------------------------------------------------------
    @api.model
    def _saldo_a_fecha(self, fecha):
        """Deuda por cobrar tal como se veia al cierre de `fecha`.

        No se puede usar amount_residual (es el saldo de HOY): se reconstruye
        restando de cada apunte solo las conciliaciones cuya max_date es
        anterior o igual a la fecha de corte. Verificado: con fecha = hoy
        devuelve exactamente lo mismo que la suma de amount_residual.
        """
        companies = tuple(self.env.companies.ids) or (0,)
        self.env.cr.execute(SQL(
            """
            WITH base AS (
                SELECT aml.id AS id, aml.partner_id AS partner_id, aml.balance AS balance
                  FROM account_move_line aml
                  JOIN account_account acc ON acc.id = aml.account_id
                  JOIN res_partner rp ON rp.id = aml.partner_id
                 WHERE acc.account_type = 'asset_receivable'
                   AND aml.parent_state = 'posted'
                   AND aml.company_id IN %(companies)s
                   AND COALESCE(rp.trixo_excluir_deudores, FALSE) = FALSE
                   AND aml.date <= %(fecha)s
            ), saldos AS (
                SELECT b.partner_id,
                       SUM(
                           b.balance
                           - COALESCE((SELECT SUM(p.amount) FROM account_partial_reconcile p
                                        WHERE p.debit_move_id = b.id AND p.max_date <= %(fecha)s), 0)
                           + COALESCE((SELECT SUM(p.amount) FROM account_partial_reconcile p
                                        WHERE p.credit_move_id = b.id AND p.max_date <= %(fecha)s), 0)
                       ) AS saldo
                  FROM base b
              GROUP BY b.partner_id
            )
            SELECT COALESCE(SUM(saldo), 0.0), COUNT(*)
              FROM saldos
             WHERE saldo > 0.005
            """,
            companies=companies,
            fecha=fecha,
        ))
        total, cantidad = self.env.cr.fetchone()
        return float(total or 0.0), int(cantidad or 0)

    # ------------------------------------------------------------------
    # Datos del tablero
    # ------------------------------------------------------------------
    @api.model
    def trixo_get_dashboard_data(self):
        self.browse().check_access("read")
        Partner = self.sudo()
        # sudo() saltea las ir.rule multi-compania: el alcance se fija a mano
        # con las companias activas del selector, igual que _saldo_a_fecha() y
        # que las listas a las que se entra con un clic (que NO van con sudo).
        # Sin esto el tablero sumaba todas las companias y el clic mostraba
        # una lista vacia para los deudores de una compania no activa.
        en_companias = [("company_id", "in", self.env.companies.ids)]

        deudores = Partner.search(en_companias + [("saldo", ">", 0)], order="saldo desc")
        a_favor = Partner.search(en_companias + [("saldo", "<", 0)])

        total = sum(deudores.mapped("saldo"))
        tramos_campos = [
            ("a30", "b_a30"),
            ("a60", "b_a60"),
            ("a90", "b_a90"),
            ("a180", "b_a180"),
            ("mas180", "b_mas180"),
        ]
        etiquetas = dict(BUCKETS)
        tramos = []
        base_pct = max(sum(abs(sum(deudores.mapped(f))) for _k, f in tramos_campos), 1.0)
        for key, campo in tramos_campos:
            monto = sum(deudores.mapped(campo))
            tramos.append({
                "key": key,
                "label": etiquetas.get(key, key),
                "amount": monto,
                "pct": round(abs(monto) * 100.0 / base_pct, 1),
            })

        # Vencido: se cuenta desde la fecha del comprobante, igual que los tramos.
        venc_90 = sum(d.b_a180 + d.b_mas180 for d in deudores)
        venc_90_cant = len([d for d in deudores if (d.b_a180 + d.b_mas180) > 0.005])
        venc_180 = sum(deudores.mapped("b_mas180"))
        venc_180_cant = len([d for d in deudores if d.b_mas180 > 0.005])

        top = [{
            "id": d.partner_id.id,
            "name": (d.partner_id.display_name or "").strip(),
            "ref": d.partner_ref or "",
            "saldo": d.saldo,
            "dias": d.dias_max,
            "pct": round(d.saldo * 100.0 / max(total, 1.0), 1),
        } for d in deudores[:TOP_N]]

        hoy = date.today()
        cierre_anterior = hoy.replace(day=1) - timedelta(days=1)
        saldo_anterior, deudores_anterior = self._saldo_a_fecha(cierre_anterior)
        delta = total - saldo_anterior
        pct_delta = round(delta * 100.0 / saldo_anterior, 1) if saldo_anterior else 0.0

        moneda = self.env.company.currency_id

        return {
            "currency_id": moneda.id,
            "fecha": hoy.strftime("%d/%m/%Y"),
            "total": total,
            "deudores": len(deudores),
            "venc_90": venc_90,
            "venc_90_cant": venc_90_cant,
            "venc_180": venc_180,
            "venc_180_cant": venc_180_cant,
            "a_favor": abs(sum(a_favor.mapped("saldo"))),
            "a_favor_cant": len(a_favor),
            "tramos": tramos,
            "top": top,
            "mes": {
                "anterior": saldo_anterior,
                "deudores_anterior": deudores_anterior,
                "delta": delta,
                "pct": pct_delta,
                "corte": cierre_anterior.strftime("%d/%m/%Y"),
            },
        }
