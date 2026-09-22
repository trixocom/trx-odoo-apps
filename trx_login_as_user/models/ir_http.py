# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request

from ..tools import GROUP_XMLID, ORIGIN_SESSION_KEY


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Expone al cliente si puede suplantar y si esta suplantando.

        El icono del systray se dibuja con esto, sin un RPC extra. El dato es
        solo para la interfaz: el permiso se vuelve a verificar en el servidor
        en cada accion.
        """
        info = super().session_info()
        origin_uid = request.session.get(ORIGIN_SESSION_KEY) if request else False
        info['trx_login_as'] = {
            'can_switch': self.env.user.has_group(GROUP_XMLID),
            'origin_uid': origin_uid or False,
        }
        return info
