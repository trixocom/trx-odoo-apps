# Part of Trixocom.
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

#: modelo -> reporte PDF a enviar
DOC_REPORTS = {
    "sale.order": "sale.action_report_saleorder",
    "purchase.order": "purchase.action_report_purchase_order",
    "account.move": "account.account_invoices",
    "stock.picking": "stock.action_report_delivery",
}


class WhatsappCompose(models.TransientModel):
    _name = "whatsapp.compose"
    _description = "Enviar documento por WhatsApp"

    res_model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)
    record_name = fields.Char(string="Documento", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Destinatario", required=True)
    phone = fields.Char(string="Número")
    wa_account_id = fields.Many2one(
        "whatsapp.account", string="Cuenta WhatsApp", required=True,
        default=lambda self: self.env["whatsapp.account"].search([], limit=1))
    body = fields.Text(string="Mensaje")
    attach_document = fields.Boolean(string="Adjuntar PDF del documento", default=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        model = self.env.context.get("active_model")
        rid = self.env.context.get("active_id")
        if model and rid:
            rec = self.env[model].browse(rid)
            res["res_model"] = model
            res["res_id"] = rid
            res["record_name"] = rec.display_name
            partner = rec.partner_id if "partner_id" in rec._fields else False
            if partner:
                res["partner_id"] = partner.id
                res["phone"] = partner.mobile or partner.phone or ""
        return res

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.phone = self.partner_id.mobile or self.partner_id.phone or ""

    def _get_number(self):
        raw = self.phone or self.partner_id.mobile or self.partner_id.phone or ""
        num = re.sub(r"\D", "", raw or "")
        if not num:
            raise UserError(_("El destinatario no tiene número de teléfono cargado."))
        return num

    def _render_document_pdf(self):
        report_ref = DOC_REPORTS.get(self.res_model)
        report = self.env.ref(report_ref, raise_if_not_found=False) if report_ref else False
        if not report:
            return None, None
        pdf, _dummy = report._render_qweb_pdf(report.report_name, [self.res_id])
        name = (self.record_name or "documento").replace("/", "_").replace(" ", "_")
        return name + ".pdf", pdf

    def action_send(self):
        self.ensure_one()
        number = self._get_number()
        channel = self.env["discuss.channel"]._get_or_create_whatsapp_channel(
            self.wa_account_id, number, self.partner_id.name)
        attachments = []
        if self.attach_document:
            fname, pdf = self._render_document_pdf()
            if pdf:
                attachments.append((fname, pdf))
        if not attachments and not (self.body or "").strip():
            raise UserError(_("Escribí un mensaje o adjuntá el documento."))
        # message_post en el canal WhatsApp -> el saliente lo manda por WhatsApp
        # y queda registrado en la conversación del contacto.
        channel.message_post(
            body=self.body or "",
            attachments=attachments,
            message_type="comment",
            author_id=self.env.user.partner_id.id,
        )
        return {"type": "ir.actions.act_window_close"}
