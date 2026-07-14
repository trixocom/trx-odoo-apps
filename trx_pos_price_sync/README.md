# trx_pos_price_sync

Sincronización en vivo de precios/productos del backend hacia las sesiones POS
abiertas (Odoo 19).

## Problema

El POS de Odoo 19 es *offline-first*: carga productos, precios y tarifas en
IndexedDB al abrir la sesión y no vuelve a consultar el servidor mientras la
sesión siga abierta. Un cambio de precio en el backend no se ve en el POS
hasta usar "Actualizar datos" **en cada terminal**.

## Solución

Módulo 100% servidor (sin JS). Al modificar campos relevantes de
`product.template` / `product.product` (precio de venta, impuestos, nombre,
código, barcode, disponibilidad POS, categorías POS) o al crear/modificar
`product.pricelist.item`, se acumulan los ids en la transacción y en precommit
se llama a `pos.config.notify_synchronisation()` (canal websocket
`SYNCHRONISATION` nativo) para cada POS con sesión abierta. El cliente aplica
los registros en vivo y los persiste en IndexedDB — el cambio sobrevive a un F5.

- Una sola notificación por transacción (aguanta actualizaciones masivas).
- Filtra por config: dominio estándar de carga de productos y tarifas
  disponibles de cada POS.
- Los mensajes viajan con el commit: sin commit, sin notificación.
- Un fallo de sincronización jamás rompe la escritura (log + continue).

## Limitación conocida

**Eliminar** una regla de tarifa no se propaga (el pipeline estático del POS
no soporta borrado remoto). Alternativas: ponerle fecha de fin a la regla
(sí se sincroniza) o "Actualizar datos" en el POS.
