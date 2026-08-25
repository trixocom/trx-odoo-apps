# Stock Packaging Invoice Report

Módulo para Odoo 18 que agrega la columna "Cantidad de Embalaje" en el reporte de facturas.

## Versión 18.0.1.0.3

### Características

* Agrega columna "Cantidad de Embalaje" en reportes de factura PDF
* Cálculo automático basado en configuración de `stock_packaging_report`
* Compatible con estructura de reportes de Odoo 18

### Dependencias

* `stock_packaging_report` - Configuración del tipo de embalaje
* `account` - Módulo de contabilidad

### Instalación

1. Instalar `stock_packaging_report`
2. Configurar nombre del embalaje en Inventario > Configuración
3. Instalar este módulo
4. Los reportes de factura mostrarán la columna automáticamente

### Autor

**Trixocom** - www.trixocom.com
