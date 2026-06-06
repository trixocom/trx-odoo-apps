# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Type - No Fiscal',
    'version': '19.0.1.1.0',
    'category': 'Sales',
    'summary': 'Tipo de pedido "No fiscal": fuerza impuestos configurables '
               '(IVA 0% / Exento) y lista de precios en la orden de venta',
    'description': """
Sale Order Type - No Fiscal
===========================

Extiende el modulo OCA ``sale_order_type`` agregando, a nivel del Tipo de
Pedido de Venta (``sale.order.type``):

* Un tilde **No fiscal**.
* Un campo **Impuestos No fiscal** (Many2many de impuestos de venta) que se
  configura en el mismo tipo de pedido.

Comportamiento
--------------
* Cuando se elige en una orden de venta un Tipo de Pedido con **No fiscal**
  tildado, todas las lineas de la orden toman automaticamente los impuestos
  configurados en **Impuestos No fiscal** (tipicamente IVA 0% / Exento), de
  modo que sean ventas libres de impuestos pero que igual figuren en los
  reportes contables de IVA / impuestos.
* Si el campo de impuestos se deja vacio, las lineas quedan **sin impuesto**.
* La **lista de precios** se cambia automaticamente usando el campo
  ``pricelist_id`` que el tipo de pedido ya provee de base (sale_order_type).
* Si el tipo de pedido **no** tiene No fiscal tildado, el comportamiento es el
  habitual de Odoo.

Tecnico
-------
* Se sobrescribe ``sale.order.line._compute_tax_ids`` llamando a ``super()`` y
  forzando los impuestos solo en las lineas cuyo pedido usa un tipo No fiscal.
* No se modifica logica de negocio del core; se respeta que el campo
  ``tax_ids`` siga siendo editable manualmente.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale_order_type',
    ],
    'data': [
        'views/sale_order_type_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
