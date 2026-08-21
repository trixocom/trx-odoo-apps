# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom
# License OPL-1 (see LICENSE file at repository root).
{
    'name': 'Panel de Control de Cobranzas',
    'version': '19.0.1.0.2',
    'author': 'Trixocom',
    'license': 'OPL-1',
    'category': 'Accounting/Payment',
    'summary': (
        'Tablero gerencial en tiempo real de las cobranzas recurrentes: '
        'facturado, cobrado, pendiente y rechazos en rojo (SIRO Banco '
        'Roela y PAGOS360), con seguimiento de cada rechazo.'
    ),
    'description': """
Panel de Control de Cobranzas
=============================
Vista gerencial de la cobranza de suscripciones:

* KPIs del mes: facturado, cobrado, pendiente, vencido y efectividad.
* Rechazos en ROJO con motivo (falta de fondos, CBU inválido, tarjeta),
  consolidando SIRO Banco Roela y PAGOS360.
* Facturas pendientes de débito, resaltando las vencidas.
* Actualización automática cada 60 segundos.
""",
    'depends': ['payment_siro_roela'],
    'data': [
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trx_cobranza_dashboard/static/src/dashboard.js',
            'trx_cobranza_dashboard/static/src/dashboard.xml',
            'trx_cobranza_dashboard/static/src/dashboard.scss',
        ],
    },
    'application': True,
    'installable': True,
}
