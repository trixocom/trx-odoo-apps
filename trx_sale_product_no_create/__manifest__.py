# -*- coding: utf-8 -*-
{
    'name': 'Venta - No crear productos desde la linea de pedido',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Quita las opciones "Crear" y "Crear y editar" del buscador de '
               'producto en la linea del pedido de venta; si no existe, lista vacia.',
    'description': """Venta - No crear productos desde la linea de pedido
===================================================

En la linea de un pedido de venta, al tipear/escanear un producto que no
existe, el autocompletado ofrece "Crear" y "Crear y editar", lo que facilita
generar productos basura por error (p.ej. al escanear un codigo de barras que
no encuentra el producto).

Este modulo agrega ``no_create`` a los campos de producto de la linea
(``product_template_id`` y ``product_id``), de modo que el buscador solo
muestre coincidencias reales y, si no hay, la lista quede vacia (sin opciones de
creacion). No afecta la creacion de productos desde el modulo de Inventario /
Ventas > Productos.

Tecnico
-------
* Hereda ``sale.view_order_form`` y setea ``options={..., 'no_create': True}``
  en los campos ``product_template_id`` y ``product_id`` de la linea.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
