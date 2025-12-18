# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [18.0.1.0.2] - 2025-10-17

### Corregido
- **Templates incorrectos**: Versión anterior heredaba de `account.report_invoice_document` que no afectaba a reportes personalizados
- **XPath inefectivo**: El CSS no se estaba aplicando a todos los reportes

### Cambiado
- **Approach ultra-agresivo**: Ahora hereda directamente de `web.external_layout_standard` y `web.report_layout`
- **CSS más fuerte**: Selectores con `!important` y mayor especificidad
- **Soporte universal**: Funciona con report_invoice_document, report_invoice_copy, report_invoice_copy_1 y cualquier variante
- **Prioridad 999**: Asegura que los estilos sobrescriban cualquier otro CSS

### Agregado
- Dependencia de módulo `web` en el manifest
- CSS @media print para forzar estilos en impresión
- Selectores para clases Bootstrap (mt-*, mb-*, pt-*, pb-*)

### Técnico
- Herencia de `web.external_layout_standard` (template base de todos los reportes)
- Herencia de `web.report_layout` (layout global de reportes)
- XPath `//div[@class='header']` con position="after" (más confiable)
- XPath `//head` para agregar estilos globales

## [18.0.1.0.1] - 2025-10-17

### Corregido
- **XPath incompatible**: Se eliminaron XPaths específicos que no existían en Odoo 18
  - Removido: `//div[hasclass('row')][@name='header-row']` (no existe en Odoo 18)
  - Removido: `//div[@id='informations']` (estructura puede variar)
  - Removido: `//table[@name='invoice_line_table']` (nombre puede variar)
  
### Cambiado
- **Approach simplificado**: Ahora usa solo CSS inline en lugar de XPaths complejos
- **Mejor compatibilidad**: El template hereda de `account.report_invoice_document` con prioridad 99
- **Sin SCSS externo**: Se eliminó la dependencia de archivos SCSS, todo el CSS está inline
- **Manifest actualizado**: Removida sección `assets` que causaba referencias a archivos inexistentes

### Técnico
- Cambio de múltiples XPath con modificaciones de atributos → Un solo XPath con tag `<style>`
- Uso de `position="before"` en lugar de `position="attributes"` para evitar errores de localización
- CSS aplicado mediante selectores globales en lugar de modificaciones específicas de elementos

## [18.0.1.0.0] - 2025-10-17

### Añadido
- Versión inicial del módulo
- Herencia del template `account.report_invoice_document`
- Estilos SCSS para optimizar espaciado
- Reducción de espacio entre encabezado y datos del cliente
- Optimización de tablas y márgenes

### Problemas Conocidos (Solucionado en v1.0.1)
- XPaths incompatibles con la estructura real de Odoo 18
- Referencias a archivos SCSS que causaban problemas en instalación

---

## Formato de Versiones

El formato de versión es: `ODOO_VERSION.MAJOR.MINOR.PATCH`

- **ODOO_VERSION**: 18.0 (versión de Odoo)
- **MAJOR**: Cambios mayores o incompatibles
- **MINOR**: Nueva funcionalidad compatible con versiones anteriores
- **PATCH**: Correcciones de bugs y mejoras menores

## Tipos de Cambios

- **Añadido**: Para nuevas funcionalidades
- **Cambiado**: Para cambios en funcionalidad existente
- **Obsoleto**: Para funcionalidad que será removida
- **Removido**: Para funcionalidad removida
- **Corregido**: Para corrección de bugs
- **Seguridad**: Para parches de seguridad
