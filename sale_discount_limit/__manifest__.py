# -*- coding: utf-8 -*-
{
    'name': 'Sale Discount Limit',
    'version': '18.0.1.0.2',
    'category': 'Sales',
    'summary': 'Control de descuentos máximos por usuario en órdenes de venta',
    'description': """
        Control de Descuentos Máximos por Usuario
        ==========================================
        
        Este módulo permite:
        * Asignar descuentos máximos permitidos por usuario
        * Validar automáticamente que no se supere el límite de descuento
        * Mostrar mensajes de error amigables al usuario
        
        Características:
        ----------------
        * Configuración individual de descuento máximo por usuario
        * Validación en tiempo real al crear/modificar líneas de orden de venta
        * Mensajes de error claros indicando el límite asignado
        * Compatible con todos los flujos de trabajo estándar de Odoo
    """,
    'author': 'Trixocom',
    'website': '',
    'license': 'GPL-3',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
