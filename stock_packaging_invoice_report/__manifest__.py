# -*- coding: utf-8 -*-
{
    'name': 'Stock Packaging Invoice Report',
    'version': '18.0.1.0.3',
    'category': 'Accounting/Accounting',
    'summary': 'Agrega columna de cantidad de embalaje al reporte de factura',
    'description': """
        Stock Packaging Invoice Report
        ==============================
        
        Este módulo extiende la funcionalidad del módulo stock_packaging_report 
        para mostrar la cantidad de embalajes en el reporte de factura.
        
        Características:
        ---------------
        * Agrega una columna "Cantidad de Embalaje" en las líneas de factura
        * Utiliza el mismo parámetro de sistema que stock_packaging_report
        * Calcula automáticamente la cantidad de embalajes según:
          - Cantidad de producto en la línea de factura
          - Unidades por embalaje definidas en el producto
          - Nombre del embalaje configurado en el sistema
        
        Dependencias:
        ------------
        * stock_packaging_report (módulo padre)
        * account (módulo de contabilidad)
        
        Configuración:
        -------------
        1. Instalar el módulo stock_packaging_report primero
        2. Configurar el nombre del embalaje en:
           Inventario > Configuración > Ajustes > Nombre del Embalaje para Stock
        3. Definir los embalajes en cada producto con el nombre configurado
        
        Uso:
        ----
        Al crear una factura, aparecerá automáticamente la columna 
        "Cantidad de Embalaje" mostrando el cálculo correspondiente.
        
        Changelog v1.0.3:
        -----------------
        * FIX: Eliminada vista innecesaria account_move_views.xml
        * Solo mantiene modelo y template de reporte
    """,
    'author': 'Trixocom',
    'website': 'www.trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'stock_packaging_report',
        'account',
    ],
    'data': [
        'report/account_invoice_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
