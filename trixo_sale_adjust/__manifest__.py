# -*- coding: utf-8 -*-
{
    'name': 'Trixocom Ajuste de Pedidos Confirmados',
    'version': '19.0.1.5.1',
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
  columna "Devuelve". Antes de confirmar muestra, linea por linea,
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
19.0.1.3.1: la lista de embalajes de "En embalaje" incluye la unidad base
del producto. `product.uom_ids` son solo los embalajes adicionales, asi que
faltaba justo el caso principal (devuelve un bulto, se lleva 2 unidades).

19.0.1.4.0: la columna "Nueva cantidad" pasa a ser "Devuelve". Antes habia que
cargar la cantidad que QUEDABA en la linea, una cuenta que el de mostrador no
tiene por que hacer y que se presta a error (pedido 4, devuelve 1, habia que
escribir 3). Ahora se carga lo que el cliente devuelve y el resto se calcula
solo; "Queda" sigue disponible como columna opcional. Consecuencia: desde el
wizard ya no se puede SUBIR la cantidad -lo agregado va por las lineas del
pedido, como ya indicaba el cartel-. El dialogo se abre en extra-large y se
estira al ancho de la ventana para que no se corten las columnas.

19.0.1.5.0: todo cambio a un pedido confirmado pasa por el wizard (decision de
Tito 22-09-2026).
* Las lineas de un pedido confirmado ya no se editan desde el formulario:
  readonly en la vista y control del lado servidor en sale.order.write
  (crear, borrar o cambiar producto, embalaje, cantidad, precio, descuento o
  impuestos). "Actualizar precios" tampoco corre sobre un pedido confirmado.
  El superusuario y el propio wizard no se bloquean.
* "Se lleva" sin tope: sirve para canjear y para vender mas del mismo
  producto, en cualquier embalaje. En el mismo embalaje de la linea se
  compensa con lo que devuelve (devuelve 1 bulto, se lleva 3: factura por 2,
  sin NC).
* Seccion "Agregar productos" para lo que no estaba en el pedido.
* Lo que el cliente se lleva se factura SIEMPRE si el pedido ya tenia
  facturas (sin opcion para no facturar), con el diario de la factura de
  origen: el de la linea que devuelve para "Se lleva", el de la ultima
  factura del pedido para un producto agregado. Diario fiscal: queda en
  borrador para revisar y pedir el CAE. En un pedido nunca facturado lo
  agregado queda pendiente y se factura con el resto.
* Precio y descuento de lo nuevo salen de las reglas vigentes (lista de
  precios, recargo por embalaje): ya no se copia el descuento manual de la
  linea de origen.
* Si lo que se agrega completaria un combo/surtido, el wizard avisa; no lo
  arma (el modulo de surtidos tampoco arma combos en pedidos confirmados).
19.0.1.5.1: las lineas se congelan recien cuando el pedido tiene una factura
de cliente vigente (borrador o confirmada), no al confirmar (decision de Tito
22-09-2026). Caja y oficina agregan productos a pedidos recien confirmados,
antes de facturar, con el cliente en el mostrador: eso sigue como antes.
Campo calculado ``trixo_lines_locked`` para la vista; mismo criterio en
sale.order.write y en "Actualizar precios".

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
            'trixo_sale_adjust/static/src/scss/sale_order_adjust.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
