# -*- coding: utf-8 -*-
{
    'name': 'Trixocom Solicitud de forzado de stock',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Forzar disponibilidad solo con aprobacion: el empleado pide, '
               'un responsable aprueba, y nada sale con stock negativo',
    'description': """
Trixocom Solicitud de forzado de stock
======================================

Reemplaza el "Forzar disponibilidad" libre de ``stock_ux`` (ADHOC) por un
circuito de solicitud y aprobacion:

* En el despacho que no tiene stock aparece el boton **"Solicitar forzar
  stock"**. El empleado escribe el motivo (obligatorio) y puede adjuntar una
  foto (en el celular abre la camara).
* El aprobador configurado en el tipo de operacion (o, si no hay, todos los
  usuarios del grupo *Aprobar forzado de stock*) recibe: un pop-up en Odoo si
  esta conectado (o al entrar, mientras la solicitud siga pendiente), una
  notificacion en la campanita con actividad, la notificacion push del
  celular si tiene Odoo instalado como app, y un WhatsApp si el modulo
  ``trixo_whatsapp`` esta instalado y hay una cuenta conectada.
* **Aprobar** fuerza la disponibilidad (el despacho queda "Disponible") y lo
  valida el empleado por el circuito normal. **Rechazar** deja el despacho en
  espera. En los dos casos el que pidio recibe la respuesta y todo queda en el
  chatter del despacho: quien pidio, motivo, foto, quien decidio y cuando.

Ademas cierra todos los caminos para dejar stock negativo:

* El boton original de ``stock_ux`` se oculta, y llamarlo por RPC da
  ``AccessError`` fuera de una aprobacion.
* Al validar cualquier movimiento que sale de una ubicacion interna se
  verifica que el stock no quede negativo (formulario, tipeo manual de
  cantidades, app de codigo de barras, transferencias internas, desechos).
  Solo se exceptua el despacho con solicitud aprobada. Configurable por
  compania (Inventario > Configuracion > "Bloquear stock negativo").

No modifica codigo de ADHOC: hereda ``stock_ux``.

Author
------
Trixocom - https://www.trixocom.com
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'stock_ux',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/stock_force_request_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_picking_type_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trx_stock_force_request/static/src/js/force_request_service.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
