{
    'name': 'POS - Sincronizacion de precios en vivo',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Empuja cambios de precios/productos/reglas de tarifa del backend '
               'a todas las sesiones POS abiertas, en vivo via bus, sin necesidad '
               'de tocar Actualizar datos en cada terminal',
    'description': """
Al modificar en el backend el precio de venta, impuestos, nombre, codigo o
disponibilidad POS de un producto, o al crear/modificar reglas de lista de
precios, todas las sesiones POS abiertas reciben los registros actualizados
por websocket (canal SYNCHRONISATION nativo de Odoo 19) y los aplican en vivo
en memoria e IndexedDB. No requiere JS propio: usa pos.config.notify_synchronisation
y el pipeline estandar del POS (connectNewData + persistencia IndexedDB).

Limitacion conocida: ELIMINAR una regla de tarifa no se propaga (el POS no
soporta borrado remoto de registros estaticos); en ese caso usar fecha de fin
en la regla (se sincroniza) o Actualizar datos en el POS.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['point_of_sale'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
