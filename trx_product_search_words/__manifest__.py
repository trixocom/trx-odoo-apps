# -*- coding: utf-8 -*-
{
    'name': 'Producto - Buscar por palabras (estilo website)',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Busca productos por palabras sueltas, en cualquier orden, en los '
               'autocompletados (lineas de venta, compra, inventario), igual que '
               'el buscador del sitio web.',
    'description': """
Producto - Buscar por palabras (estilo website)
===============================================

De fabrica, el autocompletado de un producto (por ejemplo en la linea de una
orden de venta) hace un unico ``ILIKE`` sobre el texto completo escrito. Por eso
"milan toma doble" no encuentra el producto "TOMACORRIENTE DOBLE MILAN ...":
las palabras estan en otro orden y separadas por otras palabras.

El buscador del **sitio web** (``website._search_build_domain``) en cambio parte
el texto en palabras y exige que **cada palabra** aparezca en alguno de los
campos buscables (AND de palabras, OR de campos). Este modulo lleva ese mismo
comportamiento a los autocompletados del backend.

Comportamiento
--------------
* Cuando se escriben **dos o mas palabras** (operador ``like`` / ``ilike``),
  cada palabra debe matchear en alguno de los campos nativos del producto
  (nombre, referencia interna, codigo de barras, variantes, info de proveedor),
  sin importar el orden ni que esten contiguas.
* La busqueda de **una sola palabra** y las busquedas exactas o por patron
  (``=``, ``=ilike``, etc.) quedan **identicas** al estandar.

Tecnico
-------
* ``product.template._search_display_name``: ante varios terminos, combina con
  ``AND`` el dominio nativo de cada palabra (reutiliza el metodo del core, no se
  hardcodean campos).
* ``product.product.name_search``: el ``name_search`` del core es custom y no
  pasa por ``_search_display_name`` para el termino completo, por lo que se
  adapta del mismo modo (AND de los dominios nativos por palabra).
* No se modifica codigo del core; solo se heredan los dos metodos.
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
