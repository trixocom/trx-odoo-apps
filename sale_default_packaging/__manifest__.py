# -*- coding: utf-8 -*-
{
    'name': 'Sale Default Packaging',
    'version': '19.0.2.3.0',
    'category': 'Sales',
    'summary': 'Venta por Bultos: setea la unidad de embalaje por defecto en '
               'las líneas de venta y muestra el Total Bultos',
    'description': """
Venta por Bultos sobre el modelo de UoM de Odoo 19
==================================================

En Odoo 19 product.packaging no existe: los embalajes son unidades de
medida relativas (uom.uom con relative_factor) vinculadas al producto via
product.template.uom_ids ("Packagings").

Comportamiento (identico al 18 para el usuario):
- Al elegir un producto en la linea de venta, la unidad pasa automaticamente
  al embalaje por defecto del producto (parametro
  stock_packaging_report.packaging_name, ej "Bulto") con cantidad 1.
- La columna "Cantidad" queda expresada en Bultos (es la UoM de la linea).
- Columna opcional "Unidades" (solo lectura) con la conversion a unidades.
- "Total Bultos" grande en el encabezado del pedido y en el PDF.

Notas de migracion 18 -> 19:
- product_packaging_id / product_packaging_qty desaparecen: la UoM de la
  linea ES el embalaje y product_uom_qty ES la cantidad de embalajes.
- Se conserva la clave de parametro stock_packaging_report.packaging_name
  por continuidad con los datos migrados de prod (valor: "Bulto").

Version 2.0.0: reescritura completa para Odoo 19 CE (packaging -> UoM).
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'stock',
        'product',
    ],
    'data': [
        'data/config_parameter.xml',
        'views/sale_order_views.xml',
        'views/report_saleorder.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
