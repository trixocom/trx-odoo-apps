# -*- coding: utf-8 -*-
{
    'name': 'Venta - No crear productos desde la linea de pedido',
    'version': '19.0.2.0.0',
    'category': 'Sales',
    'summary': 'Restringe por usuario la creacion de productos desde el buscador '
               'de la linea del pedido de venta.',
    'description': """
Venta - No crear productos desde la linea de pedido (selectivo por usuario)
===========================================================================

En la linea de un pedido de venta, al tipear/escanear un producto que no
existe, el autocompletado ofrece "Crear" y "Crear y editar", lo que facilita
generar productos basura por error (p.ej. al escanear un codigo de barras que
no encuentra el producto).

Por defecto, este modulo quita esas opciones para TODOS los usuarios. Con el
permiso *Ventas Trixocom > Crear productos desde la linea de pedido* se puede
habilitar la creacion solo a los usuarios elegidos.

Comportamiento
--------------
* Usuario SIN el permiso: el buscador de producto en la linea solo muestra
  coincidencias reales; si no hay, la lista queda vacia (sin "Crear").
* Usuario CON el permiso: conserva "Crear" y "Crear y editar".

No afecta la creacion de productos desde Inventario / Ventas > Productos.

Tecnico
-------
* Override de ``sale.order._get_view``: para los usuarios que no pertenecen al
  grupo ``group_sale_product_create`` se agrega ``no_create: True`` a las
  opciones de los campos ``product_template_id`` y ``product_id`` de la linea.
  Es dinamico por usuario (no duplica campos ni usa grupos a nivel de vista,
  no soportados en vistas de extension en Odoo 19).
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'security/sale_product_create_security.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
