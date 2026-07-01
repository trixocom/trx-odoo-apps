# Part of Trixocom.
from datetime import timedelta

from odoo import _, api, fields, models


class WhatsappCall(models.Model):
    """Registro de una llamada de voz por WhatsApp (softphone en vivo).

    Modelo propio de Trixocom para Odoo Community sobre el transporte WhatsApp
    (sidecar fork WuzAPI + meowcaller). La máquina de estados
    y los métodos de ciclo de vida son comandados por el softphone (OWL) y por el
    webhook de eventos del sidecar. Ver ARQUITECTURA-LLAMADAS.md.
    """

    _name = "whatsapp.call"
    _inherit = ["mail.thread.main.attachment"]
    _description = "Llamada WhatsApp"
    _order = "create_date desc"

    # Identidad de la llamada del lado del sidecar/meowcaller (32 hex). Único.
    call_id = fields.Char(string="Call ID", index=True, copy=False, readonly=True)

    wa_account_id = fields.Many2one(
        "whatsapp.account", string="Cuenta", index=True, ondelete="set null",
        readonly=True)
    partner_id = fields.Many2one("res.partner", string="Contacto", index=True)
    user_id = fields.Many2one(
        "res.users", string="Usuario", index=True,
        default=lambda self: self.env.uid)
    discuss_channel_id = fields.Many2one(
        "discuss.channel", string="Canal", ondelete="set null",
        help="Canal de Discuss de WhatsApp asociado, si lo hay.")

    phone_number = fields.Char(string="Número", required=True, readonly=True)
    direction = fields.Selection(
        selection=[("incoming", "Entrante"), ("outgoing", "Saliente")],
        string="Dirección", default="outgoing", readonly=True)
    state = fields.Selection(
        selection=[
            ("aborted", "Cancelada"),
            ("calling", "Llamando"),
            ("ringing", "Timbrando"),
            ("ongoing", "En curso"),
            ("missed", "Perdida"),
            ("rejected", "Rechazada"),
            ("terminated", "Finalizada"),
        ],
        string="Estado", default="calling", index=True, readonly=True)

    start_date = fields.Datetime(string="Inicio", readonly=True)
    duration = fields.Float(string="Duración (h)", readonly=True,
        help="Duración de la llamada en horas (decimal).")
    end_date = fields.Datetime(string="Fin", compute="_compute_end_date")

    # Las actividades se borran de la BD al marcarse hechas; conservamos el nombre.
    activity_name = fields.Char(
        string="Actividad", help="Nombre de la actividad relacionada, si la hay.")

    call_count = fields.Integer(
        string="Nº llamadas al número", compute="_compute_call_count",
        help="Total de llamadas registradas al mismo número o contacto.")

    _sql_constraints = [
        ("call_id_unique", "unique(call_id)",
         "Ya existe una llamada con ese Call ID."),
    ]

    # ------------------------------------------------------------------ #
    #  Computes
    # ------------------------------------------------------------------ #
    @api.depends("start_date", "duration")
    def _compute_end_date(self):
        for call in self:
            if call.start_date and call.duration:
                call.end_date = call.start_date + timedelta(hours=call.duration)
            else:
                call.end_date = False

    @api.depends("partner_id", "phone_number")
    def _compute_call_count(self):
        for call in self:
            if not call.phone_number and not call.partner_id:
                call.call_count = 0
                continue
            domain = [("phone_number", "=", call.phone_number)]
            if call.partner_id:
                domain = ["|", ("partner_id", "=", call.partner_id.id)] + domain
            call.call_count = self.search_count(domain)

    @api.depends("state", "direction", "partner_id.name", "phone_number",
                 "activity_name")
    def _compute_display_name(self):
        for call in self:
            call.display_name = call._build_display_name()

    def _build_display_name(self):
        self.ensure_one()
        if self.activity_name:
            return self.activity_name
        who = self.partner_id.name or self.phone_number or _("desconocido")
        if self.state == "aborted":
            return _("Llamada cancelada a %(who)s", who=who)
        if self.state == "missed":
            return _("Llamada perdida de %(who)s", who=who)
        if self.state == "rejected":
            if self.direction == "incoming":
                return _("Llamada rechazada de %(who)s", who=who)
            return _("Llamada rechazada a %(who)s", who=who)
        if self.direction == "incoming":
            return _("Llamada de %(who)s", who=who)
        return _("Llamada a %(who)s", who=who)

    # ------------------------------------------------------------------ #
    #  Máquina de estados (comandada por softphone / webhook del sidecar)
    # ------------------------------------------------------------------ #
    def start_call(self):
        """La llamada pasó a activa (audio fluyendo)."""
        self.check_access("read")
        self.sudo().write({
            "state": "ongoing",
            "start_date": fields.Datetime.now(),
        })
        return self._store_result()

    def end_call(self, activity_name=None):
        """Cierre normal; calcula duración desde start_date."""
        self.check_access("read")
        now = fields.Datetime.now()
        for call in self.sudo():
            duration = 0.0
            if call.start_date:
                duration = (now - call.start_date).total_seconds() / 3600.0
            vals = {"state": "terminated", "duration": duration}
            if activity_name:
                vals["activity_name"] = activity_name
            call.write(vals)
        return self._store_result()

    def reject_call(self):
        self.check_access("read")
        self.sudo().state = "rejected"
        return self._store_result()

    def miss_call(self):
        self.check_access("read")
        self.sudo().state = "missed"
        return self._store_result()

    def abort_call(self):
        """El originador cortó antes de que el otro extremo contestara."""
        self.check_access("read")
        self.sudo().state = "aborted"
        return self._store_result()

    def set_ringing(self):
        self.check_access("read")
        self.sudo().state = "ringing"
        return self._store_result()

    # ------------------------------------------------------------------ #
    #  Helpers para el softphone (JS)
    # ------------------------------------------------------------------ #
    @api.model
    def create_and_format(self, phone_number=None, partner_id=None,
                          direction="outgoing", wa_account_id=None,
                          call_id=None, res_id=None, res_model=None):
        """Crea una llamada y la devuelve formateada para el softphone.

        Si se pasa un registro (res_model/res_id) se introspecciona su partner.
        """
        self.check_access("read")
        vals = {
            "phone_number": phone_number,
            "partner_id": partner_id,
            "direction": direction,
            "state": "calling" if direction == "outgoing" else "ringing",
            "user_id": self.env.uid,
            "wa_account_id": wa_account_id,
            "call_id": call_id,
        }
        if res_id and res_model and not partner_id:
            record = self.env[res_model].browse(res_id)
            record.check_access("read")
            partners = record._mail_get_partners(introspect_fields=True).get(
                record.id, [])
            if partners:
                vals["partner_id"] = partners[0]
        call = self.sudo().create(vals)
        return call._store_result()

    @api.model
    def get_recent_phone_calls(self, search_terms=None, offset=0, limit=None):
        domain = [("user_id", "=", self.env.uid)]
        if search_terms:
            fields_to_search = ["phone_number", "partner_id.name", "activity_name"]
            domain += ["|", "|"] + [
                (f, "ilike", search_terms) for f in fields_to_search]
        calls = self.search(domain, offset=offset, limit=limit,
                            order="create_date desc")
        return [call._call_format() for call in calls]

    @api.model
    def _get_number_of_missed_calls(self):
        return self.search_count([
            ("user_id", "=", self.env.uid), ("state", "=", "missed")])

    def get_contact_info(self):
        """Resuelve el partner por número (llamada entrante sin contacto)."""
        self.ensure_one()
        number = (self.phone_number or "").strip()
        if not number:
            return False
        partner = self.env["res.partner"].search(
            ["|", ("phone", "=", number), ("mobile", "=", number)], limit=1)
        if partner:
            self.check_access("read")
            self.sudo().partner_id = partner
        return self._store_result()

    # ------------------------------------------------------------------ #
    #  Serialización mínima para el softphone
    # ------------------------------------------------------------------ #
    def _call_format(self):
        self.ensure_one()
        return {
            "id": self.id,
            "call_id": self.call_id,
            "display_name": self.display_name,
            "phone_number": self.phone_number,
            "direction": self.direction,
            "state": self.state,
            "partner_id": self.partner_id.id or False,
            "partner_name": self.partner_id.name or False,
            "start_date": self.start_date and fields.Datetime.to_string(
                self.start_date) or False,
            "duration": self.duration,
            "create_date": fields.Datetime.to_string(self.create_date),
        }

    def _store_result(self):
        return [call._call_format() for call in self]
