# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError

# Codigo ARCA/AFIP de la alicuota "IVA 0%" (account.tax.group.l10n_ar_vat_afip_code).
VAT_ZERO_AFIP_CODE = "3"


class AccountMove(models.Model):
    _inherit = "account.move"

    def _trx_vat_zero_lines(self):
        """Lineas de producto de la factura que llevan IVA 0% (codigo ARCA 3)."""
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
            and any(
                tax.tax_group_id.l10n_ar_vat_afip_code == VAT_ZERO_AFIP_CODE
                for tax in line.tax_ids.flatten_taxes_hierarchy()
            )
        )

    def _trx_check_vat_zero(self):
        """No dejar validar facturas fiscales argentinas con lineas en IVA 0%.

        Solo facturas y notas de debito de cliente (``out_invoice``): las notas
        de credito quedan fuera para poder anular comprobantes ya emitidos con
        IVA 0%.
        """
        for move in self:
            if move.move_type != "out_invoice" or move.country_code != "AR":
                continue
            journal = move.journal_id
            if not journal.l10n_latam_use_documents or journal.trx_allow_vat_zero:
                continue
            lines = move._trx_vat_zero_lines()
            if not lines:
                continue
            detail = "\n".join(
                "- %s" % (line.name or line.product_id.display_name or "").split("\n")[0]
                for line in lines[:8]
            )
            if len(lines) > 8:
                detail += "\n- ... (%s lineas mas)" % (len(lines) - 8)
            raise UserError(_(
                "No se puede validar la factura de %(partner)s en el diario "
                "%(journal)s: tiene %(count)s linea(s) con IVA 0%%.\n\n"
                "Un comprobante fiscal tiene que llevar IVA. No se pidio el CAE "
                "y no se consumio numeracion.\n\n"
                "Lineas con IVA 0%%:\n%(detail)s\n\n"
                "Corrija el impuesto de esas lineas (o recalcule los impuestos "
                "de la factura segun su posicion fiscal) y vuelva a validar.",
                partner=move.partner_id.display_name or "",
                journal=journal.display_name,
                count=len(lines),
                detail=detail,
            ))

    def _post(self, soft=True):
        self._trx_check_vat_zero()
        return super()._post(soft=soft)
