# -*- coding: utf-8 -*-
{
    'name': 'Trixo Partner Balance Buttons',
    'version': '19.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Smart-buttons "Adeudado" y "A Pagar" en la ficha de contacto',
    'description': """
Trixo Partner Balance Buttons
=============================

Agrega dos smart-buttons al formulario de res.partner para mostrar
el saldo de cuenta corriente del partner:

* **Adeudado**: lo que clientes adeudan (campo nativo `credit`).
* **A Pagar**: lo que se debe a proveedores (campo nativo `debit`).

Al hacer click en el botón se abre el Partner Ledger filtrado por
ese partner para ver el detalle.

Pensado para mostrar el saldo migrado desde versiones anteriores
de Odoo (donde el smart-button era estándar) en Odoo 19 Community.
""",
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['account', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
