{
    'name': 'POS - Sincronizacion de stock en vivo',
    'version': '19.0.1.0.1',
    'category': 'Sales/Point of Sale',
    'summary': 'Empuja los cambios de stock del backend a todas las sesiones '
               'POS abiertas, en vivo via bus, sin tocar Actualizar datos ni '
               'Buscar mas en cada terminal',
    'description': """
Cada cambio de cantidad en stock (recepciones, entregas, ventas del propio POS,
ajustes de inventario, transferencias internas) se propaga a todas las sesiones
POS abiertas: el POS recibe el producto re-leido con el stock del deposito de su
punto de venta (campo trx_pos_qty de trx_pos_price_display) y lo actualiza en
memoria e IndexedDB.

Reusa el mecanismo de trx_pos_price_sync: una sola notificacion por
transaccion, via el canal SYNCHRONISATION nativo de Odoo 19, sin JS propio.
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['stock', 'trx_pos_price_sync', 'trx_pos_price_display'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
