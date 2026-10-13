# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.trixo_whatsapp.drivers.base import normalize_ar_number

from .ir_rule import GROUP_XMLID


def _is_restricted(env):
    return not env.su and env.user.has_group(GROUP_XMLID)


class WhatsappAccount(models.Model):
    _inherit = 'whatsapp.account'

    # El cliente "WhatsApp Web" embebido lee TODOS los chats de la cuenta con
    # sudo. Un vendedor restringido no tiene acceso a él: sólo usa WhatsApp
    # desde el chatter de sus documentos.
    def _trx_rs_check_web_client(self):
        if _is_restricted(self.env):
            raise AccessError(_("No tenés acceso al cliente de WhatsApp. "
                                "Enviá los mensajes desde el lead, la "
                                "cotización o el cliente."))

    @api.model
    def wa_web_chats(self, *args, **kwargs):
        self._trx_rs_check_web_client()
        return super().wa_web_chats(*args, **kwargs)

    @api.model
    def wa_web_messages(self, *args, **kwargs):
        self._trx_rs_check_web_client()
        return super().wa_web_messages(*args, **kwargs)

    @api.model
    def wa_web_send(self, *args, **kwargs):
        self._trx_rs_check_web_client()
        return super().wa_web_send(*args, **kwargs)

    @api.model
    def wa_web_toggle_mute(self, *args, **kwargs):
        self._trx_rs_check_web_client()
        return super().wa_web_toggle_mute(*args, **kwargs)

    @api.model
    def wa_web_fetch_avatar(self, *args, **kwargs):
        self._trx_rs_check_web_client()
        return super().wa_web_fetch_avatar(*args, **kwargs)


class WhatsappCompose(models.TransientModel):
    _inherit = 'whatsapp.compose'

    def action_send(self):
        """Vendedor restringido: sólo desde un documento que puede ver y sólo
        al teléfono del contacto (o del documento), no a un número cualquiera."""
        if _is_restricted(self.env):
            for wizard in self:
                record = wizard._origin_record()
                if record is None:
                    raise AccessError(_(
                        "Sólo podés enviar WhatsApp desde tus leads, "
                        "cotizaciones o clientes."))
                record.check_access('read')
                wizard.partner_id.check_access('read')
                allowed = set()
                for source in (wizard.partner_id, record):
                    for fname in ('phone', 'mobile'):
                        if fname in source._fields and source[fname]:
                            num = normalize_ar_number(source[fname])
                            if num:
                                allowed.add(num)
                if wizard._get_number() not in allowed:
                    raise UserError(_(
                        "El número tiene que ser el teléfono cargado en el "
                        "contacto o en el documento."))
        return super().action_send()
