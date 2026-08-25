# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    'name': 'Stock Packaging Report',
    'version': '19.0.12.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Stock expresado en bultos: ajuste del embalaje por defecto y '
               'boton de estado en el producto',
    'description': """
Stock Packaging Report
======================

Expresa el stock en bultos en la ficha del producto y centraliza el ajuste
del embalaje por defecto que usan el resto de los modulos de bultos.

Que aporta
----------
1. **Ajuste** en Inventario > Configuracion > Ajustes > "Stock en Bultos":
   define el parametro ``stock_packaging_report.packaging_name``, que es la
   clave canonica que consumen tambien ``sale_default_packaging``,
   ``stock_packaging_invoice_report``, ``trixo_stock_packaging_display`` y
   ``trixo_internal_transfer_pkg``.
2. **Boton de estado "bultos"** en el formulario de producto y de plantilla,
   con la cantidad a mano y la pronosticada convertidas a bultos.
3. **Filtro de busqueda** "Bultos Disponibles" en Inventario > Reportes >
   Existencias, que sostiene los favoritos guardados por el cliente.
4. **Almacen por defecto del usuario**: si el usuario tiene
   ``property_warehouse_id``, las cantidades del producto se calculan sobre ese
   almacen salvo que el contexto pida uno explicito.

Migracion 18 -> 19
------------------
* ``product.packaging`` no existe en Odoo 19: el embalaje es una ``uom.uom``
  del producto (``product.uom_ids``). El calculo pasa de
  ``qty / packaging.qty`` a ``uom_id._compute_quantity(qty, bulto)``, usando el
  helper compartido ``product._trixo_default_packaging_uom()`` de
  ``sale_default_packaging``.
* El boton "Actualizar cantidad" (``action_update_quantity_on_hand``) ya no
  existe en Odoo 19: quedo fusionado dentro del boton de pronostico. En lugar
  de reemplazar el contenido de los botones del core se agrega un boton propio
  al lado, que no se rompe con cada cambio de arch del core.
* Se retiran la columna de bultos en el arbol de Existencias y el campo de
  bultos en ``stock.quant``: los provee ``trixo_stock_packaging_display``
  19.0.2.0.0 (``available_quantity_pkg`` / ``quantity_pkg`` /
  ``inventory_quantity_pkg``). Duplicarlos mostraba dos columnas iguales.
* Se retira ``models/res_users.py``, que en la v18 ya era un comentario muerto.
* La busqueda por bultos se acota a productos almacenables activos y calcula en
  lote, en lugar de hacer un ``search([])`` con una consulta por producto.

Changelog
---------
* 19.0.12.0.0: port a Odoo 19 Community sobre unidades de medida.
* 18.0.11.7.1: ultima version sobre ``product.packaging`` (Odoo 18 EE).
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'product',
        'sale_stock',
        'sale_default_packaging',
    ],
    'data': [
        'data/system_parameters.xml',
        'views/res_config_settings_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
