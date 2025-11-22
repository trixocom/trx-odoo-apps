# Changelog - POS Create SO

## [18.0.1.0.2] - 2025-11-16

### Fixed
- Ajustados imports de JavaScript para compatibilidad con Odoo 18
- Corregida referencia a `Order` en lugar de `PosOrder` inexistente
- Agregados servicios `notification` y `orm` mediante `useService` en setup()
- Corregidas referencias a propiedades del modelo Order:
  - `this.currentOrder` en lugar de `this.pos.get_order()`
  - `order.partner` en lugar de `order.get_partner()`
  - `order.lines` en lugar de `order.get_orderlines()`
- Corregido mapeo manual de líneas de orden a formato JSON compatible con backend
- Mejorado manejo condicional de UI services (block/unblock)

### Changed
- Estructura de patches JavaScript optimizada para Odoo 18
- Mejor manejo de errores con verificación de servicios disponibles
- Preparación manual de orderData en lugar de confiar en export_as_JSON
- Agregado INSTALL.md con instrucciones detalladas

## [18.0.1.0.1] - 2025-11-06

### Fixed
- Corregido ParseError en `views/pos_config_views.xml`
  - El filtro 'invoiced' no existe en la vista de búsqueda de pos.order en Odoo 18
  - Cambiada la estrategia de herencia de vistas para usar `<search position="inside">` en lugar de xpath con filtros específicos
  - Simplificada la estructura de las vistas para mejor compatibilidad

### Changed
- Actualizada información del autor a "Trixocom" con website "www.trixocom.com"
- Mejorada la documentación en el manifest

## [18.0.1.0.0] - 2025-11-06

### Added
- Versión inicial del módulo
- Botón "Crear Orden de Venta" que reemplaza el botón de pago en el POS
- Campo sale_order_id en pos.order para vincular con órdenes de venta
- Vistas backend con filtros y menú específico
- Validaciones: cliente obligatorio, productos en orden, evita duplicados
- Transferencia automática de productos, precios, descuentos e impuestos a la orden de venta
- Estilos CSS personalizados para el botón y alertas
- Scripts de instalación automática
