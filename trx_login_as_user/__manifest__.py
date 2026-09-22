# -*- coding: utf-8 -*-
{
    'name': 'Trixocom Login As User',
    'version': '19.0.1.0.1',
    'category': 'Tools',
    'summary': 'Soporte: iniciar sesion como otro usuario sin su contrasena',
    'description': """
Trixocom Login As User
======================

Permite al personal de soporte iniciar sesion como otro usuario, para reproducir
lo que ese usuario ve sin pedirle la contrasena, y volver despues a la sesion
propia. Pensado para soporte sobre instancias en produccion.

Quien puede usarlo
------------------

Solo los usuarios del grupo **Trixocom / Suplantar usuarios**
(``trx_login_as_user.group_login_as_user``), que **no se asigna a nadie al
instalar**: hay que darlo a mano. Ser Administrador de Odoo no alcanza.

El icono de la barra superior se muestra unicamente a quien tiene ese grupo (y a
quien esta suplantando, para que pueda volver).

Controles
---------

- El permiso se verifica **en el servidor** en los dos puntos de entrada (el
  asistente y la ruta de vuelta), no solo en la interfaz.
- El ACL del asistente esta restringido al grupo: un usuario sin el grupo no
  puede ni crear el registro por RPC.
- No se puede suplantar al usuario ``__system__`` (id 1), ni a usuarios
  archivados, ni a usuarios de portal o publicos.
- No se pueden encadenar suplantaciones: hay que volver al usuario propio antes
  de pasar a otro.
- La vuelta solo devuelve la sesion al usuario que inicio la suplantacion, y
  solo si ese usuario sigue activo y conserva el grupo.
- Cada ida y cada vuelta quedan registradas en el log del servidor con usuario
  de origen, usuario de destino, base de datos e IP.

No agrega campos a modelos de Odoo ni guarda historial en base: el rastro queda
en el log del servidor. Desinstalar el modulo lo revierte por completo.

Author
------
Trixocom - https://www.trixocom.com
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'AGPL-3',
    'depends': ['web'],
    'data': [
        'security/trx_login_as_user_groups.xml',
        'security/ir.model.access.csv',
        'wizard/trx_login_as_user_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trx_login_as_user/static/src/js/trx_login_as_systray.js',
            'trx_login_as_user/static/src/xml/trx_login_as_systray.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
