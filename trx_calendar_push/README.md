# Trixo Calendar Push

Recordatorios de reuniones entregados como **notificación push al celular**,
aunque el usuario no tenga Odoo abierto.

## El problema que resuelve

En Odoo 19 el recordatorio de tipo *Notificación* no se envía desde el
servidor: `calendar.alarm_manager._notify_next_alarm()` manda por el bus
(websocket) el aviso con un temporizador y **el popup lo dispara el navegador**.
Sin una pestaña de Odoo abierta y conectada, el aviso nunca aparece.

El de tipo *Correo electrónico* sí corre del lado del servidor —el cron
`calendar.ir_cron_scheduler_alarm` se auto-agenda al minuto exacto— pero llega
como un mail más, que es justo lo que uno no mira cuando está por empezar una
reunión.

## Cómo lo resuelve

Agrega un tipo de alarma `push` y lo engancha al **mismo cron nativo**, usando
el punto de extensión que el propio Odoo expone para esto:

| Pieza | Qué hace |
|---|---|
| `calendar.alarm` | suma `('push', 'Push al celular')` al campo `alarm_type` |
| `calendar.event._get_trigger_alarm_types()` | agrega `'push'` para que `_setup_alarms()` agende `cron._trigger(at=...)` |
| `calendar.alarm_manager._send_reminder()` | después del envío estándar, despacha los push del período |

Es el mismo patrón que usa el módulo estándar `calendar_sms` para su tipo
`sms`. **No se modifica código del core.**

El envío se delega en `trx_web_push`
(`trx.web.push.subscription.send_to_users`), así que no hay claves VAPID ni
service worker duplicados.

## Requisitos

* `trx_web_push` instalado.
* Cada usuario debe suscribir su dispositivo una vez desde `/trx_web_push/app`.
  En iPhone hay que agregar esa página a la pantalla de inicio **antes** de
  activar las notificaciones (restricción de Apple, no del módulo).

## Uso

En la reunión, en *Recordatorios*, elegir alguno de los predefinidos
(`Push al celular - 5 minutos`, `15 minutos`, `30 minutos`, `1 hora`, `1 día`)
o crear uno propio con tipo *Push al celular*. Se puede combinar con los
recordatorios nativos: los tipos son independientes.

El push llega a **todos los asistentes** que no hayan declinado, sean usuarios
internos y tengan al menos un dispositivo suscripto. El click abre la reunión.

## Notas

* Si el envío del push falla (red, endpoint caído), se registra en el log y
  **no** se interrumpen los recordatorios por mail ni queda el cron en error.
* En reuniones recurrentes se reagenda el trigger para la siguiente ocurrencia,
  igual que el recordatorio por mail.

---

Trixocom · https://www.trixocom.com
