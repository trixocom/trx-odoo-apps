# -*- coding: utf-8 -*-
{
    'name': 'Trixo Restrict Reset to Draft',
    'version': '18.0.1.0.0',
    'summary': 'Restringe el botón Convertir a Borrador en Facturas a un grupo específico',
    'description': """
        Este módulo oculta el botón "Convertir a borrador" (Reset to Draft) en las facturas
        para todos los usuarios excepto aquellos que pertenecen al nuevo grupo
        "Permitir convertir facturas a borrador".
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'category': 'Accounting/Accounting',
    'depends': ['account'],
    'data': [
        'security/account_security.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'license': 'GPL-3',
}
