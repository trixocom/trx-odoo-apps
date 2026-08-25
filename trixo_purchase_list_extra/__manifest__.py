{
    'name': 'Compras: fecha de creacion y estado de despacho en la lista',
    'version': '19.0.1.0.1',
    'category': 'Inventory/Purchase',
    'summary': 'Agrega las columnas Creado el y Estado de despacho a las '
               'listas de Solicitudes de cotizacion y Ordenes de compra.',
    'description': """Columnas extra en las listas de compras
=======================================

Pedido de MIRACCA sobre la v19: en la bandeja de compras se necesita ver, sin
abrir cada documento, CUANDO se creo la orden y COMO viene la recepcion de la
mercaderia.

CREADO EL
---------
Columna con `create_date` (fecha/hora real de alta del registro, no editable).
No se confunde con la columna existente "Fecha limite de la orden"
(`date_order`), que es un dato editable por el comprador y que la vista muestra
en formato relativo ("Hoy", "En 3 dias").

ESTADO DE DESPACHO
------------------
Campo calculado y almacenado `trx_receipt_state`, que resume el estado de las
transferencias de recepcion asociadas a la orden (`picking_ids`) en un solo
valor:

* Sin recepcion  - la orden todavia no genero transferencias (RFQ sin confirmar).
* Borrador / En espera / Disponible - ninguna recepcion validada todavia; se
  muestra el estado mas avanzado entre las pendientes.
* Parcial        - hay recepciones validadas y otras pendientes.
* Hecho          - todas las recepciones vigentes estan validadas.
* Cancelado      - todas las recepciones de la orden fueron canceladas.

Las transferencias canceladas no cuentan para el calculo: una orden con una
recepcion cancelada y otra validada figura como Hecho, no como Parcial.

Se eligio el estado real del picking y no el campo estandar `receipt_status` de
Odoo (Not Received / Partially / Fully) porque el deposito necesita distinguir
lo que ya esta listo para recibir de lo que todavia espera.

La columna se muestra con badge: VERDE cuando esta Hecho, ROJO en cualquier otro
estado (pedido de Tito, 25-08). Al ser un campo almacenado se puede ordenar,
filtrar y agrupar desde la
barra de busqueda.

ALCANCE
-------
Las dos listas de compras:
* `purchase.purchase_order_kpis_tree` - Compras > Ordenes > Solicitudes de cotizacion
* `purchase.purchase_order_view_tree` - Compras > Ordenes > Ordenes de compra

Solo se agregan columnas: no se toca ninguna columna existente ni ningun flujo.
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['purchase_stock'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
