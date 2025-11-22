# -*- coding: utf-8 -*-
{
    'name': 'Stock Packaging Report',
    'version': '18.0.11.7.0',
    'category': 'Inventory/Inventory',
    'summary': 'Muestra cantidad de embalajes en el reporte de Existencias y en los smart buttons del producto',
    'description': """
        Stock Packaging Report
        ======================
        
        Este módulo añade funcionalidad para mostrar cantidades en embalajes en lugar de unidades:
        
        1. Columna "Bultos Disponibles" en el reporte de Existencias 
           (Inventario > Reportes > Existencias)
        
        2. Smart Buttons del producto modificados para mostrar embalajes:
           - "Disponible": En lugar de "5.030 U", muestra "503 Cajas"
           - "Pronosticado": En lugar de "4.890 U", muestra "489 Cajas"
           (o el nombre del embalaje configurado)
        
        Funcionamiento:
        ---------------
        1. Configure el nombre del tipo de embalaje en:
           Inventario > Configuración > Ajustes > Nombre del Embalaje para Stock
        
        2. Defina los packagings en cada producto con el nombre configurado
           (pestaña Inventario > sección Embalajes)
        
        3. El sistema calculará automáticamente:
           - Disponible: qty_available / unidades_por_embalaje
           - Pronosticado: virtual_available / unidades_por_embalaje
        
        Ejemplo:
        --------
        * Configuración: Nombre del embalaje = "Caja"
        * Producto "Azúcar" tiene packaging con name="Caja" y qty=10 (10 unidades por caja)
        * Stock disponible = 5.030 unidades → Mostrará: "503 Cajas"
        * Stock pronosticado = 4.890 unidades → Mostrará: "489 Cajas"
        * En reporte de inventario: 5.030 unidades → Columna muestra: "503"
        
        Características:
        ----------------
        * Dos smart buttons modificados: "Disponible" y "Pronosticado"
        * Nueva columna "Bultos Disponibles" en Inventario > Reportes > Existencias
        * Botones ensanchados (180px) con layout optimizado para claridad
        * Configuración sencilla desde Ajustes de Inventario
        * Cálculo automático basado en los packagings ya definidos en Odoo
        * No requiere duplicar información: usa el qty existente en product.packaging
        * Compatible con Odoo 18 Enterprise Edition
        
        Changelog v11.7.0:
        ------------------
        * FIX CRÍTICO: Corregido modelo - el reporte usa product.product, NO stock.quant
        * Eliminado modelo stock_quant.py innecesario
        * La columna ahora aparece correctamente en Inventario > Reportes > Existencias
        * Usa el campo packaging_quantity_available de product.product
        
        Changelog v11.6.0:
        ------------------
        * FEATURE: Agregado modelo stock.quant con campo calculado packaging_quantity
        * FEATURE: Columna "Cantidad de Embalajes" completamente funcional en reporte de Existencias
        * Calcula automáticamente embalajes disponibles para cada línea del inventario
        * Usa la misma lógica de cálculo que los smart buttons del producto
        
        Changelog v11.5.2:
        ------------------
        * FIX: Reemplazado @class por hasclass() en xpaths para evitar warnings
        * Odoo recomienda usar hasclass() en lugar de @class='...' para mayor robustez
        * Eliminados los warnings: "Error-prone use of @class in view"
        
        Changelog v11.5.1:
        ------------------
        * FIX: Aumentado ancho de botones a 180px (era 140px, muy angosto)
        * FIX: Corregida estructura de botones - número y embalaje en misma línea
        * IMPROVE: Uso de d-flex gap-1 para espaciado correcto entre número y nombre
        
        Changelog v11.5.0:
        ------------------
        * FEATURE: Agregado botón "Pronosticado" con embalajes (packaging_virtual_available)
        * REFACTOR: Método auxiliar _calculate_packaging_qty para evitar duplicación de código
    """,
    'author': 'Trixocom',
    'website': 'https://github.com/trixocom/odoo_stock_packaging_report',
    'license': 'LGPL-3',
    'depends': ['stock', 'product'],
    'data': [
        'data/system_parameters.xml',
        'views/res_config_settings_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
