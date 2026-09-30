# trx_pos_stock_sync

Sincroniza en vivo el stock que muestra el POS (tarjeta de producto) cuando cambia
en el backend: recepciones, entregas, ventas de otro mostrador, ajustes de
inventario y transferencias internas.

- Hook en `stock.quant` (create / write de `quantity`), solo ubicaciones internas y de transito.
- Reusa el acumulador precommit de `trx_pos_price_sync`: una notificacion por transaccion.
- El POS recibe el `product.template` re-leido con `trx_pos_qty` calculado para el deposito de su PdV (`trx_pos_price_display`).
- Sin JS propio: canal `SYNCHRONISATION` nativo de Odoo 19; el cambio queda en IndexedDB y sobrevive un F5.
