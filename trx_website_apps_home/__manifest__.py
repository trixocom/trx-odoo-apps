# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    'name': 'TRX Website Apps Home',
    'version': '19.0.1.0.0',
    'summary': 'El boton de apps del sitio web lleva al home de iconos '
               'en vez de abrir un menu desplegable.',
    'description': '''TRX Website Apps Home
=====================
En el frontend del sitio web, cuando un usuario interno (base.group_user)
navega, aparece arriba a la izquierda un boton con forma de grilla
(o_frontend_to_backend_apps_btn). En Odoo 19 estandar ese boton abre un
menu desplegable (data-bs-toggle="dropdown") con la lista de aplicaciones.

Este modulo cambia ese comportamiento: el boton navega directamente al home
del backend (/odoo), es decir la pantalla con los iconos de las apps, en lugar
de desplegar el menu.

Implementacion
--------------
Hereda website.layout y:

* le quita el atributo data-bs-toggle al boton y le pone href="/odoo";
* elimina el div del menu desplegable que queda sin uso.

Cambio aditivo, reversible y sin tocar codigo fuente de Odoo. Al desinstalar
el modulo se restaura el comportamiento original.
''',
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'category': 'Website',
    'depends': ['website'],
    'data': [
        'views/website_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
