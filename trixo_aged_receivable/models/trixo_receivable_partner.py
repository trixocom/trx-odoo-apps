# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License AGPL-3.0
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from .trixo_receivable_line import BUCKET_CASE, DIAS, FROM_WHERE

# El id tiene que ser estable entre lecturas (la vista se recalcula en cada
# consulta): se compone con el contacto y la compania.
ID_EXPR = "(rp.id * 1000 + aml.company_id)"


def _bucket_sum(bucket):
    return (
        "SUM(CASE WHEN {case} = '{bucket}' THEN aml.amount_residual ELSE 0 END)"
        .format(case=BUCKET_CASE.strip(), bucket=bucket)
    )


class TrixoReceivablePartner(models.Model):
    _name = "trixo.receivable.partner"
    _description = "Deudores - resumen por cliente"
    _auto = False
    _order = "saldo desc"
    _rec_name = "partner_id"

    partner_id = fields.Many2one("res.partner", string="Cliente", readonly=True)
    partner_ref = fields.Char(string="Codigo", readonly=True)
    telefono = fields.Char(string="Telefono", readonly=True)
    vendedor_id = fields.Many2one("res.users", string="Vendedor", readonly=True)
    company_id = fields.Many2one("res.company", string="Compania", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)

    saldo = fields.Monetary(
        string="Saldo", currency_field="currency_id", readonly=True,
        help="Deuda menos saldo a favor. Es lo que el cliente debe realmente.")
    deuda = fields.Monetary(
        string="Deuda", currency_field="currency_id", readonly=True,
        help="Suma de los comprobantes impagos, sin descontar pagos a cuenta "
             "ni notas de credito sin aplicar.")
    a_favor = fields.Monetary(
        string="A favor", currency_field="currency_id", readonly=True,
        help="Pagos a cuenta y notas de credito todavia sin aplicar.")

    b_a30 = fields.Monetary(string="0-30 dias", currency_field="currency_id", readonly=True)
    b_a60 = fields.Monetary(string="31-60 dias", currency_field="currency_id", readonly=True)
    b_a90 = fields.Monetary(string="61-90 dias", currency_field="currency_id", readonly=True)
    b_a180 = fields.Monetary(string="91-180 dias", currency_field="currency_id", readonly=True)
    b_mas180 = fields.Monetary(string="+180 dias", currency_field="currency_id", readonly=True)

    dias_max = fields.Integer(
        string="Antiguedad (dias)", readonly=True, aggregator="max",
        help="Dias del comprobante impago mas antiguo.")
    fecha_mas_antigua = fields.Date(string="Comprobante mas antiguo", readonly=True)
    comprobantes = fields.Integer(string="Comprobantes", readonly=True, aggregator="sum")

    @property
    def _table_query(self) -> SQL:
        return SQL("%s %s %s", self._select(), SQL(FROM_WHERE), self._group_by())

    @api.model
    def _select(self) -> SQL:
        return SQL("""
            SELECT
                %(id_expr)s AS id,
                rp.id AS partner_id,
                rp.ref AS partner_ref,
                NULLIF(rp.phone, '') AS telefono,
                rp.user_id AS vendedor_id,
                aml.company_id AS company_id,
                comp.currency_id AS currency_id,
                SUM(aml.amount_residual) AS saldo,
                SUM(CASE WHEN aml.amount_residual > 0 THEN aml.amount_residual ELSE 0 END) AS deuda,
                SUM(CASE WHEN aml.amount_residual < 0 THEN -aml.amount_residual ELSE 0 END) AS a_favor,
                %(b_a30)s AS b_a30,
                %(b_a60)s AS b_a60,
                %(b_a90)s AS b_a90,
                %(b_a180)s AS b_a180,
                %(b_mas180)s AS b_mas180,
                MAX(%(dias)s) AS dias_max,
                MIN(aml.date) AS fecha_mas_antigua,
                COUNT(*) AS comprobantes
        """,
            id_expr=SQL(ID_EXPR),
            b_a30=SQL(_bucket_sum("a30")),
            b_a60=SQL(_bucket_sum("a60")),
            b_a90=SQL(_bucket_sum("a90")),
            b_a180=SQL(_bucket_sum("a180")),
            b_mas180=SQL(_bucket_sum("mas180")),
            dias=SQL(DIAS),
        )

    @api.model
    def _group_by(self) -> SQL:
        return SQL("""
            GROUP BY rp.id, rp.ref, rp.phone, rp.user_id,
                     aml.company_id, comp.currency_id
        """)

    def action_ver_comprobantes(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("El registro no tiene cliente asociado."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Comprobantes de %s", self.partner_id.display_name),
            "res_model": "trixo.receivable.line",
            "view_mode": "list,pivot,graph",
            "domain": [("partner_id", "=", self.partner_id.id)],
            "context": {"search_default_group_bucket": 1},
            "target": "current",
        }

    def action_ver_contacto(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.partner_id.display_name,
            "res_model": "res.partner",
            "res_id": self.partner_id.id,
            "view_mode": "form",
            "target": "current",
        }
