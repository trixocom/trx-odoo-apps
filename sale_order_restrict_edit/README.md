# Sale Order Restrict Edit

Control de permisos para editar precios y cantidades en órdenes de venta.

## Instalación

1. Actualizar lista de aplicaciones
2. Buscar "Sale Order Restrict Edit"
3. Instalar

## Configuración

**Ajustes > Usuarios y Empresas > Usuarios**
- Marcar: "Puede Modificar Precios y Cantidades en Ventas"

## Funcionamiento

**Usuario sin grupo:**
- NO puede editar price_unit ni product_uom_qty manualmente
- SÍ puede usar embalajes (compatible con sale_default_packaging)
- Los cálculos automáticos funcionan

**Usuario con grupo:**
- Control total sobre precios y cantidades

## Compatibilidad

- Odoo 18.0
- sale_default_packaging ✅
- Procesos automáticos ✅

## Autor

Trixocom - https://trixocom.com

## Licencia

LGPL-3
