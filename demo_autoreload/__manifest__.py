# -*- coding: utf-8 -*-
{
    'name': 'Demo Auto-Reload',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Módulo de demostración para probar auto-reload en desarrollo',
    'description': """
Demo Auto-Reload
================

Este módulo demuestra cómo funciona el auto-reload en Odoo 18.

Características:
----------------
* Modelo de ejemplo (demo.task)
* Vista de formulario y lista
* Menú en la aplicación
* Campos de ejemplo para modificar

Prueba el auto-reload:
----------------------
1. Instala este módulo
2. Modifica el archivo models/demo_task.py (agrega un campo nuevo)
3. Observa cómo se recarga automáticamente sin reiniciar el servidor
4. Actualiza el módulo desde la interfaz para ver los cambios en la BD

Nota: Los cambios en XML requieren actualizar el módulo.
Los cambios en Python se recargan automáticamente con --dev=all
    """,
    'author': 'Tu Nombre',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/demo_task_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
