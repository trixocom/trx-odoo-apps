# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License AGPL-3.0
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

# Tramos de antiguedad, contados desde la FECHA DEL COMPROBANTE.
BUCKETS = [
    ("a30", "0-30 dias"),
    ("a60", "31-60 dias"),
    ("a90", "61-90 dias"),
    ("a180", "91-180 dias"),
    ("mas180", "Mas de 180 dias"),
]

# Base comun de las dos vistas SQL: apuntes por cobrar sin conciliar de
# contactos no excluidos. Un unico lugar donde vive el criterio.
FROM_WHERE = """
      FROM account_move_line aml
      JOIN account_account acc ON acc.id = aml.account_id
      JOIN account_move am ON am.id = aml.move_id
      JOIN res_partner rp ON rp.id = aml.partner_id
      JOIN res_company comp ON comp.id = aml.company_id
     WHERE acc.account_type = 'asset_receivable'
       AND aml.parent_state = 'posted'
       AND aml.reconciled IS NOT TRUE
       AND aml.amount_residual != 0
       AND COALESCE(rp.trixo_excluir_deudores, FALSE) = FALSE
"""

# Expresion de antiguedad (dias desde la fecha del comprobante).
DIAS = "(CURRENT_DATE - aml.date)::int"

BUCKET_CASE = """
        CASE
            WHEN {dias} <= 30 THEN 'a30'
            WHEN {dias} <= 60 THEN 'a60'
            WHEN {dias} <= 90 THEN 'a90'
            WHEN {dias} <= 180 THEN 'a180'
            ELSE 'mas180'
        END
""".format(dias=DIAS)


class TrixoReceivableLine(models.Model):
    _name = "trixo.receivable.line"
    _description = "Deudores - detalle por comprobante"
    _auto = False
    _order = "dias desc, amount_residual desc"

    partner_id = fields.Many2one("res.partner", string="Cliente", readonly=True)
    partner_ref = fields.Char(string="Codigo", readonly=True)
    vendedor_id = fields.Many2one("res.users", string="Vendedor", readonly=True)
    move_id = fields.Many2one("account.move", string="Asiento", readonly=True)
    move_name = fields.Char(string="Comprobante", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Diario", readonly=True)
    account_id = fields.Many2one("account.account", string="Cuenta", readonly=True)
    company_id = fields.Many2one("res.company", string="Compania", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    invoice_date = fields.Date(string="Fecha", readonly=True)
    date_maturity = fields.Date(string="Vencimiento", readonly=True)
    amount_residual = fields.Monetary(
        string="Saldo", currency_field="currency_id", readonly=True)
    dias = fields.Integer(
        string="Antiguedad (dias)", readonly=True, aggregator="max",
        help="Dias transcurridos desde la fecha del comprobante.")
    dias_vencido = fields.Integer(
        string="Dias vencido", readonly=True, aggregator="max",
        help="Dias transcurridos desde la fecha de vencimiento. "
             "Negativo si todavia no vencio.")
    bucket = fields.Selection(BUCKETS, string="Tramo", readonly=True)
    tipo = fields.Selection(
        [("deuda", "Deuda"), ("favor", "Saldo a favor")],
        string="Tipo", readonly=True)

    @property
    def _table_query(self) -> SQL:
        return SQL("%s %s", self._select(), SQL(FROM_WHERE))

    @api.model
    def _select(self) -> SQL:
        return SQL("""
            SELECT
                aml.id AS id,
                aml.partner_id AS partner_id,
                rp.ref AS partner_ref,
                rp.user_id AS vendedor_id,
                aml.move_id AS move_id,
                am.name AS move_name,
                aml.journal_id AS journal_id,
                aml.account_id AS account_id,
                aml.company_id AS company_id,
                comp.currency_id AS currency_id,
                aml.date AS invoice_date,
                aml.date_maturity AS date_maturity,
                aml.amount_residual AS amount_residual,
                %(dias)s AS dias,
                (CURRENT_DATE - aml.date_maturity)::int AS dias_vencido,
                %(bucket)s AS bucket,
                CASE WHEN aml.amount_residual < 0 THEN 'favor' ELSE 'deuda' END AS tipo
        """, dias=SQL(DIAS), bucket=SQL(BUCKET_CASE))

    def action_trixo_ver_comprobante(self):
        """Abre la factura / el asiento del apunte (drill down desde el detalle)."""
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("Este apunte no tiene comprobante asociado."))
        return {
            "type": "ir.actions.act_window",
            "name": self.move_name or self.move_id.display_name,
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "current",
        }
