# -*- coding: utf-8 -*-
{
    'name': 'Partner - Razón Social',
    'version': '15.0.1.0.0',
    'category': 'Contact',
    'summary': 'Agrega campo Razón Social al partner',
    'description': """
        Partner - Razón Social
        ======================
        
        Este módulo agrega el campo 'Razón Social' al modelo res.partner.
        
        Características:
        ----------------
        * Campo 'razonsocial' en el formulario de contacto
        * Disponible para empresas y contactos
    """,
    'author': 'Trixocom',
    'website': 'https://github.com/trixocom',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
