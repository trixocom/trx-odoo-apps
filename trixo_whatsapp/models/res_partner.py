# Part of Trixocom.
import base64
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

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
