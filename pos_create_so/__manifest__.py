# -*- coding: utf-8 -*-
{
    'name': 'POS - Crear Orden de Venta en lugar de Pago',
    'version': '18.0.1.0.2',
    'category': 'Point of Sale',
    'summary': 'Reemplaza el botón de pago con la funcionalidad de crear orden de venta',
    'description': """
        Este módulo modifica el comportamiento del POS para:
        - Ocultar el botón de pago estándar
        - Agregar un botón para crear orden de venta directamente
        - No requiere proceso de pago en el POS
        
        Versión 18.0.1.0.2:
        - Ajustados assets para compatibilidad con Odoo 18
        - Corregida estructura de patches JavaScript
        - Optimizado flujo de creación de órdenes de venta
        
        Versión 18.0.1.0.1:
        - Corregido error de ParseError en vistas XML
        - Simplificada herencia de vistas para mejor compatibilidad
    """,
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'depends': [
        'point_of_sale',
        'sale',
    ],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_create_so/static/src/app/screens/payment_screen/payment_screen.js',
            'pos_create_so/static/src/app/screens/payment_screen/payment_screen.xml',
            'pos_create_so/static/src/css/payment_screen.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
