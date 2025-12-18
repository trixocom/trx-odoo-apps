# -*- coding: utf-8 -*-
{
    'name': 'Sale Barcode Scanner',
    'version': '18.0.1.0.3',
    'category': 'Sales',
    'summary': 'Escanear códigos de barras para agregar productos en órdenes de venta',
    'description': """
Sale Barcode Scanner
====================

Este módulo permite agregar productos a órdenes de venta escaneando códigos de barras.

Características:
----------------
* Campo de escaneo en formulario de orden de venta
* Búsqueda automática de productos por código de barras
* Agregar productos automáticamente a líneas de orden
* Incrementar cantidad si el producto ya existe
* Compatible con lectores de código de barras USB
* Funciona sin necesidad de JavaScript adicional

Uso:
----
1. Abre o crea una orden de venta
2. En el campo "Escanear Código de Barras" en la parte superior
3. Escanea el código de barras del producto con tu lector USB
4. El producto se agregará automáticamente a las líneas de orden
5. Si el producto ya existe, se incrementará la cantidad

Requisitos:
-----------
* Los productos deben tener configurado su código de barras
* Lector de código de barras USB (funciona como teclado)
* Módulo 'sale' instalado

Notas:
------
* El lector USB emula el teclado, no requiere configuración especial
* El campo de escaneo se limpia automáticamente después de procesar
* Muestra notificaciones cuando se agregan productos o hay errores
    """,
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['sale', 'product', 'sale_default_packaging'],
    'data': [
        'security/sale_barcode_scanner_groups.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
