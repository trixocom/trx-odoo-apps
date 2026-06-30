# Part of Trixocom.
import logging

from odoo import fields, models

from ..drivers.base import WhatsAppTransportError

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    channel_type = fields.Selection(
        selection_add=[("whatsapp", "WhatsApp")],
        ondelete={"whatsapp": "cascade"})
    wa_account_id = fields.Many2one("whatsapp.account", string="Cuenta WhatsApp",
        index=True, copy=False)
    whatsapp_number = fields.Char(string="Número WhatsApp", index=True, copy=False)
    whatsapp_partner_id = fields.Many2one("res.partner", string="Contacto WhatsApp",
        copy=False)

    # ------------------------------------------------------------------ #
    #  Canal: buscar o crear
    # ------------------------------------------------------------------ #
    def _get_or_create_whatsapp_channel(self, account, number, sender_name=False):
        channel = self.sudo().search([
            ("wa_account_id", "=", account.id),
            ("whatsapp_number", "=", number),
        ], limit=1)
        if channel:
            return channel
        partner = self._find_or_create_whatsapp_partner(number, sender_name)
        partners = partner + account.notify_user_ids.partner_id
        members = [(0, 0, {"partner_id": p.id}) for p in partners]
        # Usamos channel_type 'channel' para que Discuss lo liste en la barra
        # (el tipo propio 'whatsapp' requiere parche JS, pendiente). El ruteo
        # saliente se decide por wa_account_id, no por el tipo.
        channel = self.sudo().create({
            "name": sender_name or number,
            "channel_type": "channel",
            "wa_account_id": account.id,
            "whatsapp_number": number,
            "whatsapp_partner_id": partner.id,
            "channel_member_ids": members,
        })
        return channel

    def _find_or_create_whatsapp_partner(self, number, sender_name=False):
        Partner = self.env["res.partner"].sudo()
        partner = Partner.search([("phone", "=", "+" + number)], limit=1) \
            or Partner.search([("phone", "like", number)], limit=1)
        if not partner:
            partner = Partner.create({
                "name": sender_name or ("+" + number),
                "phone": "+" + number,
            })
        return partner

    # ------------------------------------------------------------------ #
    #  Saliente: cuando un agente escribe en un canal WhatsApp
    # ------------------------------------------------------------------ #
    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)
        for channel in self:
            if not channel.wa_account_id:
                continue
            # No reenviar lo que entró desde WhatsApp.
            if kwargs.get("message_type") == "whatsapp_message":
                continue
            if message.author_id == channel.whatsapp_partner_id:
                continue
            channel._whatsapp_send_outbound(message)
        return message

    def _whatsapp_send_outbound(self, message):
        self.ensure_one()
        transport = self.wa_account_id._get_transport()
        number = self.whatsapp_number
        body = _strip_html(message.body or "")
        WaMsg = self.env["whatsapp.message"].sudo()
        try:
            uid = None
            if message.attachment_ids:
                # Primera adjunto lleva el texto como caption; resto van solos.
                for idx, att in enumerate(message.attachment_ids):
                    caption = body if idx == 0 else None
                    uid = transport.send_media(number, att, caption=caption)
            else:
                uid = transport.send_text(number, body)
        except WhatsAppTransportError as err:
            WaMsg.create({
                "wa_account_id": self.wa_account_id.id,
                "mail_message_id": message.id,
                "mobile_number": number,
                "direction": "outbound",
                "state": "error",
                "failure_reason": str(err),
            })
            _logger.warning("WhatsApp saliente falló: %s", err)
            return
        WaMsg.create({
            "wa_account_id": self.wa_account_id.id,
            "msg_uid": uid,
            "mail_message_id": message.id,
            "mobile_number": number,
            "direction": "outbound",
            "state": "sent",
        })


def _strip_html(value):
    from odoo.tools import html2plaintext
    return html2plaintext(value) if value else ""
