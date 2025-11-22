# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Restrict Edit',
    'version': '18.0.2.0.0',
    'category': 'Sales',
    'summary': 'Restringe la edición de precios y cantidades en órdenes de venta por grupo',
    'description': """
        Control de Permisos para Edición de Precios y Cantidades en Órdenes de Venta
        ==============================================================================
        
        Este módulo permite controlar quién puede modificar los precios unitarios y 
        las cantidades en las líneas de órdenes de venta.
        
        Características:
        ================
        - Crea un grupo de seguridad "Puede Modificar Precios y Cantidades en Ventas"
        - Solo usuarios en este grupo pueden editar:
          * Precio unitario (price_unit)
          * Cantidad (product_uom_qty)
        - Los procesos automáticos siguen funcionando normalmente:
          * Cálculos automáticos de embalajes (sale_default_packaging)
          * Onchange de productos
          * Creación programática de líneas
          * Actualizaciones desde código
        
        Compatibilidad:
        ===============
        - Compatible con sale_default_packaging
        - No interfiere con procesos automáticos
        - Control solo a nivel de interfaz de usuario
        
        Configuración:
        ==============
        1. Ir a Ajustes > Usuarios y Empresas > Grupos
        2. Buscar "Puede Modificar Precios y Cantidades en Ventas"
        3. Asignar usuarios al grupo según necesidad
        
        Nota Técnica:
        =============
        - El control se aplica mediante readonly en vistas XML basado en grupos
        - No se modifica la lógica de negocio ni los métodos create/write
        - Los campos permanecen editables para procesos automáticos
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
    ],
    'data': [
        'security/sale_security.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
