# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Price Control',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Control de cambios de precio y cantidad en órdenes de venta',
    'description': """
        Control de Precios y Cantidades en Órdenes de Venta
        ======================================================
        
        Este módulo permite:
        * Restringir cambios de precio y cantidad a usuarios autorizados
        * Crear un grupo de seguridad específico
        * Permitir cambios por procesos automatizados mediante contexto
        
        Características:
        ----------------
        * Solo usuarios del grupo "Modificar Precios en Ventas" pueden cambiar precios y cantidades
        * Los procesos automatizados pueden usar contexto para bypasear la restricción
        * Compatible con todos los flujos de trabajo estándar de Odoo
    """,
    'author': 'Hector',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale_management'],
    'data': [
        'security/sale_order_security.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
