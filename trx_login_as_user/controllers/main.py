# -*- coding: utf-8 -*-
import logging

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request

from ..tools import GROUP_XMLID, ORIGIN_SESSION_KEY

_logger = logging.getLogger(__name__)


class TrxLoginAsUserController(http.Controller):
    """Vuelta a la sesion propia.

    Va aparte del asistente porque la ejecuta el usuario suplantado, que no
    tiene el grupo: lo que se verifica aca no es el grupo de quien llama, sino
    que la sesion tenga marcado un usuario de origen valido.
    """

    @http.route('/trx_login_as/back', type='jsonrpc', auth='user')
    def back(self):
        session = request.session
        origin_uid = session.get(ORIGIN_SESSION_KEY)
        if not origin_uid:
            raise AccessError(_("Esta sesion no proviene de una suplantacion."))

        origin = request.env['res.users'].sudo().browse(origin_uid).exists()
        if not origin or not origin.active or not origin.has_group(GROUP_XMLID):
            # El usuario de origen fue archivado o perdio el permiso mientras
            # tanto: no se le devuelve la sesion, se cierra.
            _logger.warning(
                "TRX LOGIN AS: vuelta rechazada a uid=%s (inactivo o sin "
                "permiso); se cierra la sesion [db=%s ip=%s]",
                origin_uid, request.env.cr.dbname,
                request.httprequest.remote_addr)
            session.logout(keep_db=True)
            return {'url': '/web/login'}

        _logger.warning(
            "TRX LOGIN AS: %s (uid=%s) vuelve a su sesion %s (uid=%s) "
            "[db=%s ip=%s]",
            request.env.user.login, request.env.uid, origin.login, origin.id,
            request.env.cr.dbname, request.httprequest.remote_addr)

        session.pop(ORIGIN_SESSION_KEY, None)
        session['pre_login'] = origin.login
        session['pre_uid'] = origin.id
        session.finalize(request.env)
        return {'url': '/odoo'}
