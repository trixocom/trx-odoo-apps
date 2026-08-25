# -*- coding: utf-8 -*-
{
    'name': 'Stock Packaging Invoice Report',
    'version': '19.0.2.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Cantidad de embalaje (bultos) en lineas y PDF de factura',
    'description': """
Stock Packaging Invoice Report
==============================

Muestra la cantidad de embalajes (bultos) en las lineas de factura, el
Total Bultos en el encabezado del form y ambos en el PDF.

Odoo 19: el modulo tercero stock_packaging_report fue ABSORBIDO
(aprobado 2026-07-12). El parametro stock_packaging_report.packaging_name
y el helper de embalaje por defecto viven en sale_default_packaging
(product._trixo_default_packaging_uom). La cantidad de bultos es la
cantidad de la linea convertida a la unidad de embalaje del producto.

Version 2.0.0: reescritura para Odoo 19 CE (packaging -> UoM); depende de
sale_default_packaging en lugar de stock_packaging_report; sin herencias
de plantillas Studio (workstream aparte).
    """,
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale_default_packaging',
        'account',
    ],
    'data': [
        'views/account_move_views.xml',
        'report/account_invoice_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
