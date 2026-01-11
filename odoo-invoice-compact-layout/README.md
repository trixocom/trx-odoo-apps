# 📦 Invoice Compact Layout - Odoo 19

[![Version](https://img.shields.io/badge/version-19.0.1.1.0-blue.svg)](https://github.com/trixocom/odoo-invoice-compact-layout)
[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo](https://img.shields.io/badge/Odoo-19.0-purple.svg)](https://www.odoo.com)

## 🎯 ¿Qué hace este módulo?

Reduce **drásticamente** el espacio entre el encabezado de la empresa y la información del cliente en los reportes de factura de Odoo 19, optimizando el uso del papel sin perder legibilidad.

### ✅ Versión 1.1.0 - SOLUCIÓN DEFINITIVA

**🎉 TODOS LOS ERRORES XML RESUELTOS**

**Cambio v1.1.0:**
- 🔧 **Usando formato `<record>`** en lugar del shortcut `<template>`
- ✅ Odoo 19 requiere el formato estándar `<record>` para herencia de vistas
- ✅ Estructura XML 100% compatible
- ✅ **ESTE FORMATO SÍ FUNCIONA** ✓

**Templates soportados:**
- ✅ `account.report_invoice_copy_1` (template principal)
- ✅ Compatible con localización argentina
- ✅ Compatible con customizaciones de Studio

## 🚀 Instalación Rápida

```bash
# Si ya lo tienes instalado, ACTUALIZA:
cd /mnt/extra-addons/odoo-invoice-compact-layout
git pull origin main

# Si es NUEVO:
cd /mnt/extra-addons
git clone https://github.com/trixocom/odoo-invoice-compact-layout.git

# Reinicia Odoo
systemctl restart odoo
```

### En Odoo:
1. **Modo Desarrollador** → Configuración → Activar (`?debug=1`)
2. **Apps** → ⋮ → **Actualizar lista de aplicaciones**
3. Buscar **"Invoice Compact Layout"**
4. Click en **Instalar** (o **Actualizar** si ya estaba)
5. ¡Abrir una factura y ver los cambios!

## 📋 Características

### CSS Ultra-Compacto
- ✅ Reset completo de header (margin/padding = 0)
- ✅ Article sin padding superior
- ✅ Eliminación total de espacios en company_address
- ✅ Rows compactas (0mm margin/padding)
- ✅ Anulación de TODOS los margins Bootstrap
- ✅ Anulación de TODOS los paddings Bootstrap
- ✅ Ocultación de divs vacíos
- ✅ Compactación de .oe_structure (Studio)
- ✅ Line-height de 1.1 global
- ✅ Tablas optimizadas

### Ventajas
- **Compatible** con Odoo 19 ✓
- **Formato estándar** `<record>` de Odoo
- **No afecta** otros reportes
- **Herencia limpia** mediante XPath
- **Sobrescribe** customizaciones de Studio
- **Fácil desinstalación**

## 🛠️ Solución de Problemas

### ⚠️ Error XML

**✅ RESUELTO en v1.1.0**

Si actualizaste de una versión anterior:
```bash
cd /mnt/extra-addons/odoo-invoice-compact-layout
git pull origin main
systemctl restart odoo
```

Luego en Odoo → Apps → Invoice Compact Layout → **Actualizar**

### No veo cambios

1. **Verifica instalación:** Apps → "Invoice Compact" → debe decir "Instalado"
2. **Limpia caché:** Ctrl + F5 (Windows/Linux) o Cmd + Shift + R (Mac)
3. **Reinicia Odoo:**
   ```bash
   systemctl restart odoo
   ```
4. **Verifica la vista:** Configuración → Técnico → Vistas → buscar `report_invoice_copy_1_ultra_compact`

### Necesito MÁS compactación

Edita `views/report_invoice_compact.xml` y cambia:
- `padding-top: 1mm` → `padding-top: 0mm`
- `line-height: 1.1` → `line-height: 1.0`

Luego actualiza el módulo.

## 📝 Estructura

```
odoo-invoice-compact-layout/
├── __init__.py
├── __manifest__.py
└── views/
    └── report_invoice_compact.xml   (✅ v1.1.0 - Formato <record>)
```

## 📊 Changelog

### v1.1.0 (2025-10-17) - SOLUCIÓN DEFINITIVA ✅
- 🔧 **FIXED:** Usando formato `<record>` en lugar de `<template>`
- ✅ Odoo 19 requiere este formato estándar
- ✅ Sin errores XML
- ✅ Instalación exitosa

### v1.0.9 (2025-10-17)
- 🔧 Removido tag `<data>` (causó conflicto)
- ❌ Formato `<template>` no compatible con Odoo 19

### v1.0.8 (2025-10-17)
- 🔧 Agregado tag `<data>` (causó error)

### v1.0.7 (2025-10-17)
- 🔧 Corregido position en xpath

### v1.0.0 (2025-10-17)
- 🎉 Release inicial

## 🔗 Links

- [Repositorio GitHub](https://github.com/trixocom/odoo-invoice-compact-layout)
- [Reportar Bug](https://github.com/trixocom/odoo-invoice-compact-layout/issues)
- [Documentación Odoo 19](https://www.odoo.com/documentation/19.0/)

## 👨‍💻 Autor

**TrixoCom**
- GitHub: [@trixocom](https://github.com/trixocom)
- Email: hectorquiroz@trixocom.com

## 📄 Licencia

LGPL-3.0

---

⭐ **Si este módulo te fue útil, dale una estrella en GitHub!**

**Última actualización:** 2025-10-17 v1.1.0 ✅ DEFINITIVO
