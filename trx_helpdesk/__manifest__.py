# -*- coding: utf-8 -*-
{
    'name': 'Trixo Helpdesk',
    'version': '19.0.1.1.3',
    'category': 'Services/Helpdesk',
    'summary': 'Mesa de ayuda: equipos, tickets, etapas, SLA y reportes (Community)',
    'description': """
Trixo Helpdesk
==============
Módulo de mesa de ayuda (Helpdesk) para Odoo 19 Community Edition.

Inspirado en la experiencia de uso de Helpdesk Enterprise pero desarrollado
íntegramente por Trixocom para Community, sin copiar código propietario.

Funcionalidad principal
------------------------
* **Equipos de soporte** (helpdesk.team) con método de asignación
  (manual / aleatorio / balanceado), miembros y etapas propias.
* **Tickets** (helpdesk.ticket) con numeración automática, prioridad,
  estado kanban, tipo, etiquetas, cliente, responsable y seguimiento
  completo vía chatter (mensajes y actividades).
* **Etapas** (helpdesk.stage) configurables y compartidas entre equipos,
  con etapas de cierre.
* **Tipos de ticket** y **Etiquetas**.
* **Políticas de SLA** (helpdesk.sla) con objetivo de tiempo por equipo,
  prioridad y tipo; cálculo de fecha límite y estado (en curso / cumplido / vencido).
* **Tablero (Overview)** por equipo con contadores (abiertos, sin asignar,
  urgentes, SLA vencido).
* **Vistas**: Kanban, Lista, Formulario, Calendario, Pivot, Gráfico y Actividad.
* **Reportes** de análisis de tickets.
* **Seguridad**: grupos Usuario y Administrador de Helpdesk.
""",
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'license': 'LGPL-3',
    'depends': ['mail'],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_data.xml',
        'views/helpdesk_stage_views.xml',
        'views/helpdesk_ticket_type_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_sla_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_team_views.xml',
        'views/res_partner_views.xml',
        'views/helpdesk_menus.xml',
    ],
    'demo': [
        'data/helpdesk_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trx_helpdesk/static/src/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
