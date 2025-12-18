# Changelog - Stock Packaging Invoice Report

## [18.0.1.0.3] - 2025-11-16

### Fixed
- Eliminado archivo views/account_move_views.xml que causaba error de xpath
- Simplificada estructura del módulo: solo modelo + reporte
- Corregidos xpaths en reporte para Odoo 18

### Changed
- Manifest actualizado para solo incluir report/account_invoice_report.xml

## [18.0.1.0.2] - 2025-11-16

### Added
- Versión inicial funcional del módulo
- Campo computed `packaging_quantity_invoice` en account.move.line
- Template heredado de reporte de factura con columna de embalaje
