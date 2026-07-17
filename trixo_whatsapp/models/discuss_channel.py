# Part of Trixocom.
import base64
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
    whatsapp_is_group = fields.Boolean(string="Es grupo WhatsApp", copy=False)

    # ------------------------------------------------------------------ #
    #  Canal: buscar o crear
    # ------------------------------------------------------------------ #
    def _get_or_create_whatsapp_channel(self, account, number, sender_name=False,
                                        lid=False):
        channel = self.sudo().search([
            ("wa_account_id", "=", account.id),
            ("whatsapp_number", "=", number),
        ], limit=1)
        if channel:
            if lid and channel.whatsapp_partner_id:
                channel.whatsapp_partner_id._wa_set_lid(lid)
            return channel
        partner = self._find_or_create_whatsapp_partner(
            number, sender_name, account, lid=lid)
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
        # Avatar del canal = foto de perfil del contacto (si no, Discuss muestra "#").
        if partner.image_1920:
            channel.sudo().image_128 = partner.image_1920
        return channel

    def _get_or_create_whatsapp_group_channel(self, account, group_jid, group_name=False):
        """UN canal por grupo (keyed por el JID @g.us). Los mensajes de todos los
        integrantes caen acá; el autor de cada mensaje es el integrante."""
        channel = self.sudo().search([
            ("wa_account_id", "=", account.id),
            ("whatsapp_number", "=", group_jid),
        ], limit=1)
        if channel:
            if group_name and channel.name != group_name:
                channel.sudo().name = group_name
            return channel
        members = [(0, 0, {"partner_id": u.partner_id.id})
                   for u in account.notify_user_ids]
        channel = self.sudo().create({
            "name": group_name or group_jid,
            "channel_type": "channel",
            "wa_account_id": account.id,
            "whatsapp_number": group_jid,
            "whatsapp_is_group": True,
            "channel_member_ids": members,
        })
        # Foto del grupo como avatar del canal (si el grupo tiene una).
        try:
            raw = account._get_transport().fetch_avatar(group_jid)
            if raw:
                channel.sudo().image_128 = base64.b64encode(raw)
        except Exception:  # noqa: BLE001
            pass
        return channel

    def _find_or_create_whatsapp_partner(self, number, sender_name=False,
                                         account=False, lid=False):
        Partner = self.env["res.partner"].sudo()
        # Si el n\u00famero coincide con un contacto existente, se usa ese contacto;
        # si no, se crea un placeholder con el nombre que trae WhatsApp (PushName).
        partner = Partner.search([("phone", "=", "+" + number)], limit=1) \
            or Partner.search([("phone", "like", number)], limit=1)
        if not partner:
            partner = Partner.create({
                "name": sender_name or ("+" + number),
                "phone": "+" + number,
            })
        # LID de WhatsApp -> contacto: habilita resolver menciones en grupos.
        if lid:
            partner._wa_set_lid(lid)
        # Foto de perfil de WhatsApp -> imagen del contacto (si no tiene una).
        if account and not partner.image_1920:
            partner._set_whatsapp_avatar(account, number)
        return partner

    def action_open_whatsapp_partner(self):
        """Salta del chat al cliente (desde ahí, sus ventas/compras nativas)."""
        self.ensure_one()
        if not self.whatsapp_partner_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": self.whatsapp_partner_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------ #
    #  Saliente: cuando un agente escribe en un canal WhatsApp
    # ------------------------------------------------------------------ #
    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)
        # Notas internas / notificaciones (p.ej. avisos de llamada entrante/perdida)
        # NUNCA se reenvían al contacto de WhatsApp: solo comentarios de agente salen.
        if self.env.context.get("whatsapp_skip_outbound") \
                or kwargs.get("message_type") == "notification" \
                or kwargs.get("subtype_xmlid") == "mail.mt_note":
            return message
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
        # Si es respuesta a un mensaje puntual (Discuss parent_id), citar en WhatsApp.
        reply_uid = None
        if message.parent_id:
            parent_wa = WaMsg.search(
                [("mail_message_id", "=", message.parent_id.id)], limit=1)
            reply_uid = parent_wa.msg_uid or None
        try:
            uid = None
            if message.attachment_ids:
                # Primera adjunto lleva el texto como caption; resto van solos.
                for idx, att in enumerate(message.attachment_ids):
                    caption = body if idx == 0 else None
                    uid = transport.send_media(number, att, caption=caption,
                                               reply_to_uid=reply_uid if idx == 0 else None)
            else:
                uid = transport.send_text(number, body, reply_to_uid=reply_uid)
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
