# Part of Trixocom.
import logging
import secrets
import string
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..drivers.base import TRANSPORT_REGISTRY, WhatsAppTransportError

_logger = logging.getLogger(__name__)


class WhatsappAccount(models.Model):
    _name = "whatsapp.account"
    _inherit = ["mail.thread"]
    _description = "Cuenta WhatsApp (multi-conector)"

    name = fields.Char(string="Nombre", required=True, tracking=1)
    active = fields.Boolean(default=True)
    provider = fields.Selection(
        selection=[
            ("meta_cloud", "Meta Cloud API (oficial)"),
            ("whatsmeow", "whatsmeow (QR directo)"),
        ],
        string="Proveedor", required=True, default="meta_cloud", tracking=2,
        help="Transporte usado para enviar y recibir. Determina qué campos aplican.")
    phone_number = fields.Char(string="Número", readonly=True, copy=False,
        help="Número asociado a esta cuenta (se completa al conectar).")
    notify_user_ids = fields.Many2many(
        comodel_name="res.users", string="Notificar a",
        default=lambda self: self.env.user,
        domain=[("share", "=", False)],
        help="Usuarios a notificar cuando llega un mensaje sin canal activo.")
    callback_url = fields.Char(string="Callback URL", compute="_compute_callback_url")

    # --- Meta Cloud API ---
    meta_app_uid = fields.Char(string="App ID")
    meta_app_secret = fields.Char(string="App Secret",
        groups="trixo_whatsapp.group_whatsapp_admin")
    meta_account_uid = fields.Char(string="WABA Account ID")
    meta_phone_uid = fields.Char(string="Phone Number ID")
    meta_token = fields.Char(string="Access Token",
        groups="trixo_whatsapp.group_whatsapp_admin")
    meta_webhook_verify_token = fields.Char(
        string="Webhook Verify Token", compute="_compute_verify_token", store=True,
        groups="trixo_whatsapp.group_whatsapp_admin")

    # --- whatsmeow (sidecar) ---
    whatsmeow_base_url = fields.Char(string="URL del sidecar",
        help="Base REST del sidecar whatsmeow, p.ej. http://whatsmeow:8080")
    whatsmeow_token = fields.Char(string="Token del sidecar",
        groups="trixo_whatsapp.group_whatsapp_admin")
    whatsmeow_session_id = fields.Char(string="Session ID", copy=False)
    whatsmeow_state = fields.Selection(
        selection=[
            ("logged_out", "Desconectado"),
            ("qr_pending", "Esperando QR"),
            ("connected", "Conectado"),
            ("error", "Error"),
        ], string="Estado de sesión", default="logged_out", copy=False)
    whatsmeow_qr = fields.Binary(string="QR", copy=False, attachment=False,
        help="QR de login (se actualiza al pedir/refrescar; se limpia al cerrar sesión).")

    _sql_constraints = [
        ("meta_phone_uid_unique", "unique(meta_phone_uid)",
         "Ya existe una cuenta con ese Phone Number ID."),
    ]

    # ------------------------------------------------------------------ #
    #  Computes
    # ------------------------------------------------------------------ #
    def _compute_callback_url(self):
        base = self.get_base_url()
        for acc in self:
            if acc.provider == "meta_cloud":
                acc.callback_url = base + "/trixo_whatsapp/meta/webhook"
            else:
                acc.callback_url = base + "/trixo_whatsapp/whatsmeow/webhook"

    @api.depends("meta_account_uid")
    def _compute_verify_token(self):
        for acc in self:
            if acc.id and not acc.meta_webhook_verify_token:
                acc.meta_webhook_verify_token = "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(16))

    # ------------------------------------------------------------------ #
    #  Fábrica de transporte
    # ------------------------------------------------------------------ #
    def _get_transport(self):
        self.ensure_one()
        cls = TRANSPORT_REGISTRY.get(self.provider)
        if not cls:
            raise UserError(_("Proveedor no soportado: %s", self.provider))
        return cls(self)

    # ------------------------------------------------------------------ #
    #  Acciones de UI
    # ------------------------------------------------------------------ #
    def button_test_connection(self):
        self.ensure_one()
        try:
            self._get_transport().test_connection()
        except WhatsAppTransportError as err:
            raise UserError(str(err)) from err
        return self._notify(_("Conexión OK."), "success")

    def action_connect_whatsmeow(self):
        self.ensure_one()
        transport = self._get_transport()
        transport.connect()
        # WuzAPI tarda un instante en generar el QR tras conectar: lo esperamos
        # (hasta ~6s) para mostrarlo en el primer click, sin depender de "Refrescar".
        state = "logged_out"
        qr = False
        for _ in range(8):
            state = transport.status()
            if state == "connected":
                qr = False
                break
            if state == "qr_pending":
                qr = transport.get_qr()
                if qr:
                    break
            time.sleep(0.7)
        self.whatsmeow_state = state
        self.whatsmeow_qr = qr or False
        return self._reload_form()

    def _reload_form(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_refresh_qr(self):
        self.ensure_one()
        transport = self._get_transport()
        state = transport.status()
        self.whatsmeow_state = state
        self.whatsmeow_qr = transport.get_qr() if state == "qr_pending" else False
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_logout_whatsmeow(self):
        self.ensure_one()
        self._get_transport().logout()
        self.whatsmeow_state = "logged_out"
        self.whatsmeow_qr = False

    def _notify(self, message, ntype="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"type": ntype, "message": message},
        }

    # ------------------------------------------------------------------ #
    #  Entrante UNIFICADO (ambos proveedores convergen aquí)
    # ------------------------------------------------------------------ #
    def _process_inbound(self, event):
        """Procesa un evento entrante normalizado (ver drivers/base.py).

        Punto único de convergencia: encuentra/crea el canal de Discuss y postea
        el mensaje, de modo que la bandeja/chatter sean idénticos para Meta y whatsmeow.
        """
        self.ensure_one()
        Channel = self.env["discuss.channel"].sudo()

        # Reacción: aplicar sobre el mensaje original, no crear mensaje nuevo.
        # TODO(increment-2): mapear la reacción al API de reacciones de Discuss
        # (verificar la firma exacta en core mail v19.1 antes de llamarla).
        if event.get("type") == "reaction" and event.get("reaction"):
            _logger.info("Reacción WhatsApp recibida (pendiente de aplicar): %s",
                         event["reaction"])
            return

        channel = Channel._get_or_create_whatsapp_channel(
            self, event["from"], event.get("sender_name"))

        post_vals = {
            "message_type": "whatsapp_message",
            "author_id": channel.whatsapp_partner_id.id,
            "subtype_xmlid": "mail.mt_comment",
        }
        if event.get("body"):
            post_vals["body"] = event["body"]
        if event.get("attachment"):
            name, content, mimetype = event["attachment"]
            if event.get("voice"):
                # 3er elemento dict -> Odoo marca el adjunto como nota de voz
                # (reproductor inline en Discuss).
                post_vals["attachments"] = [(name, content, {"voice": True})]
            else:
                post_vals["attachments"] = [(name, content)]

        # Cita entrante: enlazar como respuesta al mensaje citado si lo tenemos.
        if event.get("reply_to_uid"):
            parent_wa = self.env["whatsapp.message"].sudo().search(
                [("msg_uid", "=", event["reply_to_uid"])], limit=1)
            if parent_wa.mail_message_id:
                post_vals["parent_id"] = parent_wa.mail_message_id.id

        message = channel.message_post(**post_vals)

        # Trazabilidad en whatsapp.message (entrante)
        self.env["whatsapp.message"].sudo().create({
            "wa_account_id": self.id,
            "msg_uid": event.get("msg_uid"),
            "mobile_number": event["from"],
            "mail_message_id": message.id,
            "state": "received",
            "direction": "inbound",
        })
        return message

    # ------------------------------------------------------------------ #
    #  Eventos de LLAMADA (fork WuzAPI + meowcaller) -> whatsapp.call
    # ------------------------------------------------------------------ #
    @staticmethod
    def _call_number(jid):
        """Extrae el número del JID del peer (549...@s.whatsapp.net / @lid)."""
        return (jid or "").split("@")[0].split(":")[0].split(".")[0]

    def _process_call_event(self, data):
        """Procesa un evento de llamada del sidecar (fork meowcaller).

        `data['type']` ∈ CallIncoming | CallState | CallEnded. Mantiene el registro
        `whatsapp.call`, avisa en el canal de Discuss y empuja por el bus (para el
        softphone, F5). Ver ARQUITECTURA-LLAMADAS.md.
        """
        self.ensure_one()
        Call = self.env["whatsapp.call"].sudo()
        ctype = data.get("type")
        call_id = data.get("call_id")
        if not call_id:
            return

        if ctype == "CallIncoming":
            if Call.search_count([("call_id", "=", call_id)]):
                return  # idempotente: ya registrada
            number = self._call_number(data.get("from"))
            channel = self.env["discuss.channel"].sudo()._get_or_create_whatsapp_channel(
                self, number, None)
            partner = channel.whatsapp_partner_id if channel else False
            call = Call.create({
                "call_id": call_id,
                "wa_account_id": self.id,
                "direction": "incoming",
                "state": "ringing",
                "phone_number": number,
                "partner_id": partner.id if partner else False,
                "discuss_channel_id": channel.id if channel else False,
            })
            if channel:
                channel.message_post(
                    body=_("📞 Llamada entrante de %s",
                           (partner.name if partner else False) or number),
                    message_type="notification", subtype_xmlid="mail.mt_note")
            self._notify_call_bus(call, "incoming")
            return call

        call = Call.search([("call_id", "=", call_id)], limit=1)
        if not call:
            return

        if ctype == "CallState":
            phase = data.get("phase")
            if phase == "active" and call.state != "ongoing":
                call.start_call()
                self._notify_call_bus(call, "ongoing")
            elif phase in ("ringing", "connecting") and call.state == "calling":
                call.set_ringing()
                self._notify_call_bus(call, "ringing")
            return call

        if ctype == "CallEnded":
            answered = bool(call.start_date) or call.state == "ongoing"
            if answered:
                call.end_call()
                if call.discuss_channel_id:
                    call.discuss_channel_id.message_post(
                        body=_("📞 Llamada finalizada (%d s)",
                               int(round(call.duration * 3600.0))),
                        message_type="notification", subtype_xmlid="mail.mt_note")
            else:
                call.miss_call()
                if call.discuss_channel_id:
                    call.discuss_channel_id.message_post(
                        body=_("📞 Llamada perdida de %s",
                               call.partner_id.name or call.phone_number),
                        message_type="notification", subtype_xmlid="mail.mt_note")
            self._notify_call_bus(call, call.state)
            return call

    def _notify_call_bus(self, call, kind):
        """Empuja el evento por el bus a los usuarios a notificar (consumido por el softphone, F5)."""
        payload = dict(call._call_format(), kind=kind, wa_account_id=self.id)
        targets = self.notify_user_ids or self.env.user
        for user in targets:
            self.env["bus.bus"]._sendone(user.partner_id, "whatsapp.call", payload)
