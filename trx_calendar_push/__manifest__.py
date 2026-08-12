# -*- coding: utf-8 -*-
{
    'name': 'Trixo Calendar Push',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Calendar',
    'summary': 'Recordatorios de reuniones por Web Push al celular (aunque Odoo esté cerrado)',
    'description': """Trixo Calendar Push
===================

Agrega a las reuniones del Calendario un tipo de recordatorio **Push**, que se
entrega como notificación al celular usando `trx_web_push` (Web Push / VAPID).

Por qué hace falta
------------------
El recordatorio nativo de tipo *Notificación* no sale del servidor: Odoo manda
por el bus (websocket) el aviso con un temporizador y **el popup lo dispara el
navegador**. Si el usuario no tiene una pestaña de Odoo abierta en ese momento,
no se entera de nada. El de tipo *Correo electrónico* sí es del lado del
servidor, pero llega como un mail más.

Qué hace este módulo
--------------------
* Suma el tipo de alarma ``push`` a ``calendar.alarm``.
* Engancha el tipo nuevo al cron nativo ``calendar.ir_cron_scheduler_alarm``
  extendiendo ``_get_trigger_alarm_types()``, el mismo punto de extensión que
  usa el módulo estándar ``calendar_sms``. No se modifica código del core.
* Al vencer el recordatorio, envía un Web Push a cada asistente que no haya
  declinado, que sea usuario interno y que tenga al menos un dispositivo
  suscripto. El click en la notificación abre la reunión en Odoo.
* Trae recordatorios push predefinidos (5, 15 y 30 minutos, 1 hora y 1 día).

Requisitos
----------
Cada usuario tiene que suscribir su dispositivo una vez desde
``/trx_web_push/app``. En iPhone hay que agregar esa página a la pantalla de
inicio antes de activar las notificaciones (restricción de Apple).
""",
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['calendar', 'trx_web_push'],
    'data': [
        'data/calendar_alarm_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
