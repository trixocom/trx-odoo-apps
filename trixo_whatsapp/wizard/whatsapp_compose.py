# Part of Trixocom.
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WhatsappCompose(models.TransientModel):
    _name = "whatsapp.compose"
    _description = "Enviar por WhatsApp"

    res_model = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)
    record_name = fields.Char(string="Origen", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Destinatario", required=True)
    phone = fields.Char(string="Número")
    wa_account_id = fields.Many2one(
        "whatsapp.account", string="Cuenta WhatsApp", required=True,
        default=lambda self: self.env["whatsapp.account"].search([], limit=1))
    body = fields.Text(string="Mensaje")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context
        model = ctx.get("active_model") or ctx.get("default_res_model")
        rid = ctx.get("active_id") or ctx.get("default_res_id")
        if model and rid and model in self.env:
            rec = self.env[model].browse(rid)
            res["res_model"] = model
            res["res_id"] = rid
            res["record_name"] = rec.display_name
            if rec._name == "res.partner":
                partner = rec
            else:
                partner = rec.partner_id if "partner_id" in rec._fields else False
            if partner:
                res.setdefault("partner_id", partner.id)
            numf = ctx.get("default_number_field_name")
            if numf and numf in rec._fields and rec[numf]:
                res["phone"] = rec[numf]
            elif partner:
                res["phone"] = partner.phone or ""
        return res

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id and not self.phone:
            self.phone = self.partner_id.phone or ""

    def _get_number(self):
        raw = self.phone or self.partner_id.phone or ""
        num = re.sub(r"\D", "", raw or "")
        if not num:
            raise UserError(_("El destinatario no tiene número de teléfono cargado."))
        return num

    def _extra_attachments(self):
        """Hook para módulos que adjuntan algo (p.ej. el PDF de un documento)."""
        return []

    def action_send(self):
        self.ensure_one()
        number = self._get_number()
        channel = self.env["discuss.channel"]._get_or_create_whatsapp_channel(
            self.wa_account_id, number, self.partner_id.name)
        attachments = self._extra_attachments()
        if not attachments and not (self.body or "").strip():
            raise UserError(_("Escribí un mensaje o adjuntá algo para enviar."))
        channel.message_post(
            body=self.body or "",
            attachments=attachments,
            message_type="comment",
            author_id=self.env.user.partner_id.id,
        )
        return {"type": "ir.actions.act_window_close"}
