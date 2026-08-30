# -*- coding: utf-8 -*-
{
    'name': 'Trixocom - Geo-barrera de Asistencias',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Bloquea el ingreso/egreso si el empleado no está en su ubicación de trabajo',
    'description': """
Geo-barrera para el control de asistencias
==========================================

* Agrega coordenadas (latitud/longitud) y radio de tolerancia a las
  Ubicaciones de trabajo (hr.work.location).
* Al fichar desde el navegador/celular (systray), valida con fórmula de
  Haversine que el empleado esté dentro del radio de su ubicación de
  trabajo asignada. Si está fuera, el ingreso/egreso se rechaza.
* Si el empleado no comparte su ubicación (GPS denegado o sin señal),
  el fichaje se bloquea: sin coordenadas válidas no hay ingreso/egreso.
* Compatible con hr_homeworking: se valida contra la ubicación que
  corresponde al día (excepción del día > día de la semana > ubicación
  de trabajo del contrato).
* El modo kiosco queda exento (el kiosco ya está físicamente en el
  lugar de trabajo).
* Casilla "Exento de geo-barrera" por empleado para supervisores o
  personal móvil.

La validación es en el servidor: no se puede saltar deshabilitando
JavaScript ni negando el permiso de ubicación.

Requiere el "Seguimiento de dispositivo y ubicación" de Asistencias
activado (se activa automáticamente al instalar).
    """,
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['hr_attendance'],
    'data': [
        'views/hr_work_location_views.xml',
        'views/hr_employee_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trx_attendance_geofence/static/src/attendance_menu/attendance_menu_patch.js',
        ],
    },
    'post_init_hook': '_enable_device_tracking',
    'installable': True,
    'application': False,
    'auto_install': False,
}
