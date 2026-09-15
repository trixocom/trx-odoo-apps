# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom - License AGPL-3.0
{
    "name": "Trixocom - Tablero de Deudores",
    "version": "19.0.2.2.2",
    "category": "Accounting",
    "summary": "Tablero de cuentas por cobrar: quien debe, cuanto y desde cuando (antiguedad de saldos)",
    "description": """
Tablero de Deudores
===================

Reemplazo Community del reporte de antiguedad de saldos (Aged Receivable) de
Odoo Enterprise. Trabaja sobre los apuntes contables sin conciliar de las
cuentas por cobrar, sin duplicar datos: los dos modelos son vistas SQL
calculadas en tiempo de consulta (_table_query), no tablas.

* Tablero de entrada con tarjetas: total adeudado, deuda de mas de 90 y de
  mas de 180 dias, y variacion contra el cierre del mes anterior; barras por
  tramo de antiguedad y ranking de los que mas deben. Todo clicable.
* Resumen por cliente: saldo neto, deuda, saldo a favor y apertura por tramos
  de antiguedad (0-30 / 31-60 / 61-90 / 91-180 / +180 dias), contados desde la
  fecha del comprobante.
* Detalle por comprobante, agrupable y graficable.
* Saldos a favor (pagos a cuenta y notas de credito sin aplicar).
* Contactos excluibles del tablero (contacto generico de mostrador, etc.).
* Menu propio y grupo de seguridad propio: solo lo ve quien tenga el permiso.

Generico: no depende de ningun modulo de cliente.
""",
    "author": "Trixocom",
    "website": "https://www.trixocom.com",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/trixo_aged_receivable_security.xml",
        "security/ir.model.access.csv",
        "views/trixo_receivable_partner_views.xml",
        "views/trixo_receivable_line_views.xml",
        "views/res_partner_views.xml",
        "views/trixo_dashboard_views.xml",
        "views/trixo_aged_receivable_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "trixo_aged_receivable/static/src/**/*",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
