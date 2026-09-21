# trx_pos_mercado_pago — Point Smart de Mercado Pago en el POS de Odoo 19 (Orders API)

Backport a Odoo 19 CE del módulo `pos_mercado_pago` de `odoo/odoo` rama `master`
(commit `c89bb6b`, 2026-09-20), que migró de la *Point Integration API*
(`/point/integration-api/...`, deprecada por Mercado Pago) a la *Orders API*
(`POST /v1/orders`, `GET /v1/orders/{id}`, `POST /v1/orders/{id}/refund`,
`GET /terminals/v1/list`, `PATCH /terminals/v1/setup`).

## Diferencias con el `pos_mercado_pago` de Odoo 19.0

| | `pos_mercado_pago` 19.0 (core) | `trx_pos_mercado_pago` |
|---|---|---|
| API | Point Integration API (deprecada) | Orders API |
| Evento del webhook en el panel de MP | "Integraciones Point" (`point_integration_wh`) | **"Order (Mercado Pago)"** (`orders`) |
| Firma del webhook | `id:{data.id};request-id;ts` | `id:{data.id en minúsculas};request-id;ts` (query param `data.id`) |
| Modo PDV | `PATCH /point/integration-api/devices/{id}` | `PATCH /terminals/v1/setup` |
| Reembolsos | no | total/parcial (`mp_order_refund`) |
| Sandbox | no documentado | credenciales de prueba + terminal virtual `SBX0000001` |
| Endpoint del webhook mostrado en el método de pago | no | sí (`mp_webhook_endpoint`) |

Los campos (`mp_bearer_token`, `mp_webhook_secret_key`, `mp_id_point_smart`,
`mp_id_point_smart_complet`) y el selector de terminal (`mercado_pago`) son los
mismos que en el módulo core, así que **no pueden convivir**: desinstalar
`pos_mercado_pago` antes de instalar este (hay un `pre_init_hook` que lo verifica).

## Flujo

1. El cajero elige el método de pago Mercado Pago en la pantalla de pago y toca
   "Enviar". Odoo crea una order tipo `point` en Mercado Pago con
   `external_reference = <session_id>_<payment_method_id>_<uuid del pedido>`,
   `print_on_terminal` implícito y expiración de 30 minutos.
2. El terminal muestra el importe; el cliente paga.
3. Mercado Pago llama a `POST <web.base.url>/pos_mercado_pago/notification`
   (firmado con la clave secreta). Odoo verifica la firma y avisa al POS por el
   bus (`MERCADO_PAGO_LATEST_MESSAGE`).
4. El POS consulta la order: `processed` → línea pagada (y si el POS tiene
   "Validar automáticamente el pago por terminal", el pedido se valida solo);
   `canceled` / `expired` / pago no `processed` → línea a reintentar.
   `action_required` → se avisa al operador y se sigue esperando.

## Configuración

Punto de venta > Configuración > Métodos de pago: diario tipo Banco, terminal
"Mercado Pago", *Production user token* (Access Token `APP_USR-...` de la app
de Mercado Pago tipo "Pagos presenciales"), *Production secret key* (clave
secreta generada al guardar el webhook en Tus integraciones > Webhooks >
Configurar notificaciones, modo productivo, evento **Order (Mercado Pago)**,
URL = el "Webhook Endpoint" que muestra el método de pago) y *Terminal S/N*
(número de serie del Point Smart; Odoo lo resuelve al id completo, p.ej.
`PAX_A910__SMARTPOS1234567890`).

El terminal debe estar en modo PDV (botón "Force PDV" en modo desarrollador, o
desde el equipo: Más opciones > Ajustes > Modo de vinculación). En modo PDV el
terminal solo acepta cobros enviados desde Odoo.

## Sandbox

Con el Access Token de prueba de la app y el terminal virtual `SBX0000001` se
puede probar sin equipo físico; el cambio de estado de la order se simula con
la API de Mercado Pago (ver "Prueba de integración" en la documentación de
Point).

## Licencia

LGPL-3. Derivado de `odoo/odoo` (Odoo S.A.), adaptado por Trixocom.
