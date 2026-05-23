# -*- coding: utf-8 -*-
# Copyright 2026 Trixocom
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "Trixocom POS - Toggle Factura en Primera Pantalla",
    "summary": "Mueve el toggle Recibo/Factura del pago a la pantalla principal "
               "del POS, en formato compacto.",
    "description": """
Trixocom POS - Toggle Factura
=============================

Quita el botón *Invoice / Recibo-Factura* de la pantalla de cobro (Payment Screen)
y lo añade — compacto, sólo icono con check de estado — en la fila de control
buttons de la pantalla principal del POS (Product Screen), al lado del botón
de Cliente.

* No cambia la lógica subyacente: sigue alternando ``order.to_invoice``.
* Respeta ``pos.config.canInvoice`` (deshabilitado si no hay diario configurado).
* Respeta el caso refund: si la orden refunda una orden ya facturada, queda
  obligatorio facturar (no se puede destildar), igual que el botón original.
""",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "author": "Trixocom",
    "website": "https://www.trixocom.com",
    "license": "LGPL-3",
    "depends": [
        "point_of_sale",
    ],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "trx_pos_invoice_toggle/static/src/components/invoice_toggle.js",
            "trx_pos_invoice_toggle/static/src/components/invoice_toggle.xml",
            "trx_pos_invoice_toggle/static/src/components/invoice_toggle.scss",
            "trx_pos_invoice_toggle/static/src/overrides/control_buttons.js",
            "trx_pos_invoice_toggle/static/src/overrides/control_buttons.xml",
            "trx_pos_invoice_toggle/static/src/overrides/payment_screen.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
