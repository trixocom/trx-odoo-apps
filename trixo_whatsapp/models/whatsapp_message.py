# Part of Trixocom.
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

#: estado del proveedor -> estado interno
STATUS_MAP = {
    "sent": "sent",
    "delivered": "delivered",
    "read": "read",
    "failed": "error",
}


class WhatsappMessage(models.Model):
    _name = "whatsapp.message"
    _description = "Mensaje WhatsApp"
    _order = "id desc"
    _rec_name = "msg_uid"

    wa_account_id = fields.Many2one("whatsapp.account", string="Cuenta",
        required=True, ondelete="cascade", index=True)
    msg_uid = fields.Char(string="UID proveedor", index=True, copy=False)
    mobile_number = fields.Char(string="Número")
    mail_message_id = fields.Many2one("mail.message", string="Mensaje Odoo",
        ondelete="cascade", index=True)
    direction = fields.Selection(
        [("inbound", "Entrante"), ("outbound", "Saliente")],
        string="Dirección", default="outbound")
    state = fields.Selection(
        [
            ("outgoing", "En cola"),
            ("sent", "Enviado"),
            ("delivered", "Entregado"),
            ("read", "Leído"),
            ("received", "Recibido"),
            ("error", "Error"),
            ("cancel", "Cancelado"),
        ], string="Estado", default="outgoing", index=True)
    failure_reason = fields.Char(string="Motivo de fallo")

    #: orden de progreso para no retroceder de estado (read no vuelve a sent)
    _STATE_RANK = {"outgoing": 0, "sent": 1, "delivered": 2, "read": 3,
                   "received": 3, "error": 4, "cancel": 4}

    def _process_statuses(self, value):
        """Procesa el array ``statuses`` de un webhook (formato Meta Cloud API).

        Cada status: {id, status, recipient_id, timestamp, errors:[{title,...}]}.
        Actualiza el whatsapp.message saliente correspondiente por ``msg_uid``,
        sin retroceder de estado.
        """
        for status in value.get("statuses", []):
            uid = status.get("id")
            new_state = STATUS_MAP.get(status.get("status"))
            if not (uid and new_state):
                continue
            message = self.sudo().search([("msg_uid", "=", uid)], limit=1)
            if not message:
                continue
            if self._STATE_RANK.get(new_state, 0) < self._STATE_RANK.get(message.state, 0):
                continue
            vals = {"state": new_state}
            if new_state == "error":
                errors = status.get("errors") or [{}]
                vals["failure_reason"] = errors[0].get("title") or errors[0].get("message")
            message.write(vals)
