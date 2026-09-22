# -*- coding: utf-8 -*-
{
    'name': 'Trixocom Ajuste de Pedidos Confirmados',
    'version': '19.0.1.3.0',
    'category': 'Sales/Sales',
    'summary': 'Cancelar pendientes, devolver y emitir notas de credito sobre '
               'un pedido confirmado desde una sola pantalla',
    'description': """
Trixocom Ajuste de Pedidos Confirmados
======================================

Reemplazo en Odoo 19 CE del "Cancelar cantidades pendientes" de
``sale_stock_ux`` (ADHOC, v18) ampliado al caso real de mostrador: el pedido
ya esta facturado, cobrado y entregado cuando el cliente cambia de idea.

Dos entradas, un solo camino:

* Boton por linea (icono prohibido, junto a la cantidad a entregar): deja la
  linea en lo entregado. Si no hay nada facturado de mas, actua en un click
  (paridad v18); si hay que emitir nota de credito, abre el wizard.
* Boton de cabecera "Ajustar pedido": wizard con todas las lineas y una
  columna "Nueva cantidad". Antes de confirmar muestra, linea por linea,
  que va a pasar (cancela pendiente / devolucion / nota de credito).

Que hace al confirmar, en este orden y en una sola transaccion:

1. Devolucion (core ``stock.return.picking``, ``to_refund=True``) por lo
   entregado de mas. Se valida en el acto si el tipo de pedido lo indica
   (mostrador) o queda pendiente para deposito (entrega a domicilio).
2. Baja la cantidad pedida: el core reduce/cancela los movimientos
   pendientes.
3. Nota de credito como reversion PARCIAL de la factura original
   (``_reverse_moves``): conserva precios e impuestos de la factura,
   descuenta ``qty_invoiced`` y deja ``reversed_entry_id`` para que la NC
   electronica salga con comprobante asociado (ARCA). Se confirma si la
   opcion esta marcada; si ARCA rechaza, la NC queda en borrador y el resto
   del ajuste se conserva.
4. Factura lo agregado al pedido (cantidades aumentadas / productos nuevos
   pendientes de facturar). Diario no fiscal: se confirma en el acto. Diario
   fiscal (AFIP/ARCA): queda en borrador y se avisa. El despacho adicional
   lo genera el core al guardar el pedido y queda listo para validar.
5. Concilia la NC contra facturas impagas de la misma orden.

19.0.1.1.0: el boton "Ajustar pedido" toma las cantidades que el usuario bajo
directamente en las lineas del pedido (sin guardarlas) y abre el wizard con
"Nueva cantidad" ya cargada; factura de lo agregado; mensaje guia al guardar
una cantidad menor a la entregada.
19.0.1.1.1: si se apreta "Ajustar pedido" sin haber modificado el pedido, un
cartel explica que primero se cambian las cantidades y despues se apreta el boton.

19.0.1.2.0: camino unico. El boton "Devolver" de las transferencias que vienen
de un pedido de venta y el boton "Nota de credito" de las facturas de cliente
quedan reservados al grupo 'Ver "Devolver" y "Nota de credito" nativos', que por
defecto no tiene nadie (views/hide_native_buttons.xml). Compras no se tocan.
El modulo pasa al repo trx-odoo-apps (antes vivia en un repo de cliente).

19.0.1.3.0: canje de embalaje. Cada linea del wizard tiene ademas "Se lleva"
+ "En embalaje": lo que el cliente se lleva del mismo producto en otro
embalaje a cambio de lo que devuelve (devuelve un bulto, se lleva 2 unidades).
Se agrega como linea nueva del pedido -una linea no puede estar en dos
embalajes a la vez-, se despacha y se factura junto con el resto del ajuste,
al precio vigente de ese embalaje (recargo por suelto incluido) y con el
descuento de la linea de origen. No se puede llevar mas de lo que se devuelve:
eso es una venta adicional y va por las lineas del pedido.
Ademas: el wizard ya no exige editar cantidades antes de abrirlo (es el punto
de entrada del ajuste), se cierra la edicion pendiente de la celda antes de
leer las cantidades bajadas, y se preserva el descuento manual de la linea que
el wizard modifica (el core lo recalculaba a 0).

Combos (modulo de surtidos, dependencia opcional): la cabecera lleva el precio y los
componentes el stock a $0. Si se toca un componente se re-evalua el combo
con la receta del surtido; si deja de aplicar, se desarma: NC por la
cabecera completa, componentes re-tasados a la lista de precios vigente y
facturados por la cantidad que el cliente se queda.

No borra lineas ni facturas, no convierte nada a borrador, no toca precios
fuera del desarme de combos. Todo lo que crea son documentos estandar de
Odoo: desinstalar el modulo no pierde nada.

Author
------
Trixocom - https://www.trixocom.com
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'AGPL-3',
    'depends': [
        'sale_stock',
        'stock_account',
        'sale_order_type',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/sale_order_adjust_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_type_views.xml',
        'views/hide_native_buttons.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trixo_sale_adjust/static/src/js/adjust_button_patch.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
