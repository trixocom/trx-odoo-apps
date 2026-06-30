# Part of Trixocom.
import logging
import secrets
import string

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
    whatsmeow_qr = fields.Char(string="QR", copy=False, store=False,
        help="QR de login (efímero, no se persiste).")

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
        return self.action_refresh_qr()

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
            post_vals["attachments"] = [(name, content)]

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
