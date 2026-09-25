# trx_website_distribuidor (Odoo 19)

Portal de distribuidores para la tienda web.

- **Grupo** `Distribuidor (portal)`: se agrega a usuarios portal.
- **Catálogo completo**: regla `Distribuidor: ve todos los productos vendibles`. Desactivarla = solo publicados.
- **Precios sin IVA** para el distribuidor (el resto ve lo configurado en el sitio).
- **Códigos de producto** en la tarjeta, la ficha y el carrito; "+ IVA" junto al precio.
- **Exclusiones**: categorías internas y marcas que el distribuidor no ve (parámetros `excluir_categorias` y `excluir_marcas`, ids separados por coma).
- **Stock**: el distribuidor ve siempre la cantidad disponible y puede pedir sin stock.
- **Retiro y pago en el local** (Click & Collect nativo): el método de entrega *en tienda* solo aparece para distribuidores; el pago en el local confirma el pedido.
- **Aviso de pedido** (cron `Distribuidores: avisar pedidos web`, se dispara al instante):
  mensaje en el pedido a todos los usuarios internos (bandeja/email + push nativo),
  push de `trx_web_push` si está instalado y WhatsApp vía `trixo_whatsapp`.

Las restricciones para vendedores (solo sus clientes, pedidos y facturas) están en el módulo horizontal `trx_sale_restricted_salesman`.

Parámetros (`ir.config_parameter`):

| Clave | Uso |
|---|---|
| `trx_website_distribuidor.wa_destinos` | Números `549...` o JID de grupo `...@g.us`, separados por coma |
| `trx_website_distribuidor.wa_activo` | `True` envía WhatsApp; cualquier otro valor solo deja constancia (entornos de prueba) |
| `trx_website_distribuidor.avisar_todos_web` | `True` avisa todo pedido web; por defecto solo distribuidores |

Autor: Trixocom · LGPL-3
