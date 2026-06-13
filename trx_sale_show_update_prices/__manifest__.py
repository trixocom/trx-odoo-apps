# -*- coding: utf-8 -*-
{
    'name': 'Sale - Mostrar siempre "Actualizar precios"',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Deja visible el boton "Actualizar precios" junto a la lista de '
               'precios en cotizaciones (presupuesto / enviado)',
    'description': """Sale - Mostrar siempre "Actualizar precios"
=============================================

De fabrica, Odoo muestra el boton **Actualizar precios** (al lado de la lista
de precios en la orden de venta) solo cuando se detecta un cambio de lista de
precios sobre un pedido que ya tiene lineas (campo ``show_update_pricelist``).
El resto del tiempo el boton queda oculto.

Este modulo deja ese boton **siempre visible mientras el pedido es una
cotizacion** (estados ``draft`` / ``sent``), para que el usuario pueda
recalcular los precios contra la lista vigente en cualquier momento sin
necesidad de cambiar la lista para que aparezca el enlace.

Comportamiento
--------------
* El boton ``action_update_prices`` se muestra siempre en cotizaciones.
* Se mantiene oculto en pedidos **confirmados** (``sale``) y **cancelados**
  (``cancel``), igual que el estandar, para no recalcular precios sobre
  ventas ya cerradas.

Tecnico
-------
* Vista heredada de ``sale.view_order_form``.
* Solo se modifica el atributo ``invisible`` del boton ya existente
  (``action_update_prices``); no se agrega logica de negocio ni se toca el
  core. La accion que recalcula los precios es la nativa de Odoo.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
