# -*- coding: utf-8 -*-
"""Constantes compartidas entre el asistente, el controlador y session_info."""

GROUP_XMLID = 'trx_login_as_user.group_login_as_user'

# uid del usuario que inicio la suplantacion, guardado en la sesion web.
ORIGIN_SESSION_KEY = 'trx_login_as_origin_uid'

# Usuario que nunca se puede suplantar.
FORBIDDEN_UIDS = (1,)
