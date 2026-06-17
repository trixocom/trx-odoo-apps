# -*- coding: utf-8 -*-
{
    'name': 'Producto - Buscar codigo de barras sin cero a la izquierda (EAN13)',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Al escanear/tipear un codigo de barras al que le falta el cero '
               'a la izquierda, completa a EAN13 y encuentra igual el producto '
               '(linea de venta, compra, inventario).',
    'description': """Producto - Buscar codigo de barras sin cero a la izquierda (EAN13)
==================================================================

Muchos EAN13 se guardan con uno o mas ceros a la izquierda (ej.
``0264709617697``), pero la etiqueta impresa a veces se imprime sin ese cero
(``264709617697``). Al escanear ese codigo en la linea de un pedido de venta,
el autocompletado nativo hace un match EXACTO sobre ``barcode`` y, al no
coincidir la longitud, no encuentra el producto.

Comportamiento
--------------
* Si la busqueda nativa NO encuentra nada y el termino es puramente numerico y
  mas corto que 13 digitos, se reintenta un match EXACTO contra el ``barcode``
  completado con ceros a la izquierda hasta 13 (``zfill(13)``).
* Si la busqueda nativa ya encontro algo, no se altera el resultado: tiene
  prioridad un producto cuyo barcode coincide tal cual (ej. un barcode de 12
  digitos propio).

Tecnico
-------
* ``product.product.name_search``: tras llamar al ``super()``, si vuelve vacio y
  el termino aplica, agrega el dominio ``('barcode', '=', term.zfill(13))``.
* No modifica codigo del core; solo hereda ``name_search``.
* Compone con ``trx_product_search_words`` (ambos llaman a ``super()``).
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'product',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
