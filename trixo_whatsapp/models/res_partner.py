# Part of Trixocom.
import base64
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    whatsapp_channel_count = fields.Integer(
        string="Chats WhatsApp", compute="_compute_whatsapp_channel_count")

    whatsapp_lid = fields.Char(
        string="WhatsApp LID", index=True, copy=False,
        help="Identificador interno de WhatsApp (@lid) del contacto. En grupos, "
             "WhatsApp identifica a los integrantes por LID y en las menciones "
             "s\u00f3lo env\u00eda ese LID (no el tel\u00e9fono ni el nombre). Guardarlo permite "
             "resolver las menciones al contacto correcto.")

    def _wa_set_lid(self, lid):
        """Guarda el LID de WhatsApp en el contacto si a\u00fan no lo tiene o cambi\u00f3."""
        lid = (lid or "").strip()
        if not lid:
            return
        for partner in self:
            if partner.whatsapp_lid != lid:
                partner.sudo().whatsapp_lid = lid

    def _compute_whatsapp_channel_count(self):
        Channel = self.env["discuss.channel"].sudo()
        for partner in self:
            partner.whatsapp_channel_count = Channel.search_count(
                [("whatsapp_partner_id", "=", partner.id)]) if partner.id else 0

    def action_open_whatsapp_channels(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chats WhatsApp"),
            "res_model": "discuss.channel",
            "view_mode": "list,form",
            "domain": [("whatsapp_partner_id", "=", self.id)],
            "context": {"create": False},
        }

    def _set_whatsapp_avatar(self, account, number):
        """Baja la foto de perfil de WhatsApp del contacto y la usa como imagen."""
        self.ensure_one()
        try:
            avatar = account._get_transport().fetch_avatar(number)
        except Exception:  # noqa: BLE001
            avatar = b""
        if not avatar:
            return
        try:
            self.sudo().write({"image_1920": base64.b64encode(avatar)})
        except Exception:  # noqa: BLE001
            _logger.info("No se pudo setear avatar WhatsApp para %s", number)
