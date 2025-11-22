# -*- coding: utf-8 -*-
{
    'name': 'Sale Default Packaging',
    'version': '18.0.1.1.2',
    'category': 'Sales',
    'summary': 'Establece embalaje por defecto en líneas de venta basándose en Stock Packaging Report',
    'description': """
        Módulo para Odoo 18 que establece automáticamente el embalaje por defecto en las líneas de venta
        
        Características:
        =================
        - Establece automáticamente el embalaje configurado en Stock Packaging Report
        - Define una cantidad de embalaje por defecto (1.0)
        - Calcula automáticamente las unidades de producto basándose en la cantidad de embalajes
        - Sincroniza bidireccionalmente las cantidades de embalajes y unidades
        - Campos adicionales en las líneas de venta:
          * Embalaje (product_packaging_id)
          * Cantidad de Embalajes (product_packaging_qty)
        
        Dependencias:
        =============
        - stock_packaging_report (https://github.com/trixocom/odoo_stock_packaging_report)
        
        Funcionamiento:
        ===============
        1. Al seleccionar un producto, busca el embalaje configurado en Stock Packaging Report
        2. Si el producto tiene ese embalaje, lo establece automáticamente
        3. La cantidad de producto se calcula como: Cant. Embalajes × Unidades por Embalaje
        4. Los cambios en cualquier campo se sincronizan automáticamente
        
        Configuración:
        ==============
        1. Instalar el módulo stock_packaging_report
        2. Configurar el nombre del embalaje en Inventario > Configuración > Ajustes
        3. Asignar embalajes a los productos con el mismo nombre configurado
        
        Versión 1.1.2:
        ==============
        - Corrección de nombre de dependencia: stock_packaging_report (no odoo_stock_packaging_report)
        
        Versión 1.1.1:
        ==============
        - Corrección de xpath en vistas XML para Odoo 18
        - Mejora en la compatibilidad con vistas de sale.order
        
        Versión 1.1.0:
        ==============
        - Refactorización completa del modelo
        - Mejora en el cálculo de cantidades
        - Sincronización bidireccional entre cantidades
        - Vista mejorada con campos más intuitivos
        - Mejor integración con stock_packaging_report
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'stock',
        'product',
        'stock_packaging_report',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
