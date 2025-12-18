# Notas Técnicas - Corrección v18.0.1.0.2

## Problema Identificado

**Error:** `ParseError` al intentar instalar el módulo
```
El elemento '<xpath expr="//field[@name='line_ids']//field[@name='quantity']">' 
no puede ser localizado en la vista padre
```

## Causa Raíz

En Odoo 18, la estructura de vistas de facturas cambió:
- **Antes (Odoo 17):** Usaba `line_ids` para líneas de factura
- **Ahora (Odoo 18):** Usa `invoice_line_ids` para líneas de factura

Los xpaths apuntaban a una estructura que ya no existe en Odoo 18.

## Solución Implementada

### 1. Corrección de XPath Principal

**Antes:**
```xml
<xpath expr="//field[@name='line_ids']//field[@name='quantity']" position="after">
```

**Después:**
```xml
<xpath expr="//field[@name='invoice_line_ids']/tree//field[@name='quantity']" position="after">
```

### 2. Atributos Actualizados para Odoo 18

**Antes:**
```xml
<field name="packaging_name" invisible="1"/>
```

**Después:**
```xml
<field name="packaging_name" column_invisible="1"/>
```

En Odoo 18, `invisible="1"` en columnas de tree se reemplaza por `column_invisible="1"`.

### 3. Simplificación de Estructura

**Eliminado:**
- Estructuras anidadas innecesarias (`<tree>`, `<form>` dentro del field)
- Atributos `attrs` que causaban conflictos
- Vista de búsqueda (search) que no era necesaria
- Menú adicional que podía causar conflictos

**Mantenido:**
- Vista de formulario con xpath simplificado
- Vista tree de account.move.line

## Archivos Modificados

1. **views/account_move_views.xml**
   - Simplificado de 60 líneas a 35 líneas
   - 2 vistas en lugar de 4
   - XPaths corregidos para Odoo 18

2. **__manifest__.py**
   - Versión actualizada a 18.0.1.0.2

3. **CHANGELOG.md**
   - Documentados cambios v18.0.1.0.2

4. **install_module.sh**
   - Actualizado número de versión

5. **INSTALL.md**
   - Actualizado número de versión

## Pruebas Recomendadas

### Test 1: Instalación
```bash
# En Odoo UI
Aplicaciones → Stock Packaging Invoice Report → Instalar
```
✓ Debe instalar sin errores

### Test 2: Vista de Factura
```bash
# En Odoo UI
Contabilidad → Facturas → Nueva Factura
```
✓ Columna "Cantidad de Embalaje" debe aparecer en líneas

### Test 3: Cálculo
```bash
# Configurar producto con embalaje de 10 unidades
# Agregar línea de 100 unidades
```
✓ Debe mostrar 10.0 en "Cantidad de Embalaje"

### Test 4: Reporte PDF
```bash
# Crear factura y hacer clic en Imprimir
```
✓ PDF debe incluir columna "Cantidad de Embalaje"

## Compatibilidad

✓ **Odoo 18.0** - Totalmente compatible
✗ **Odoo 17.0** - Requiere xpaths diferentes
✗ **Odoo 16.0** - Requiere xpaths diferentes

## Referencias

- Odoo 18 Form Views: https://www.odoo.com/documentation/18.0/developer/reference/backend/views.html
- Account Move Structure: `/usr/lib/python3/dist-packages/odoo/addons/account/views/account_move_views.xml`
- XPath en Odoo: https://www.odoo.com/documentation/18.0/developer/reference/backend/views.html#inheritance

## Lecciones Aprendidas

1. Siempre verificar la estructura de vistas en la versión específica de Odoo
2. En Odoo 18, usar `invoice_line_ids` en lugar de `line_ids` para facturas
3. Preferir xpaths simples sobre estructuras complejas
4. Usar `column_invisible` en lugar de `invisible` para columnas de tree
5. Menos herencia de vistas = menos puntos de falla

---
**Autor:** Trixocom  
**Fecha:** 2025-11-16  
**Versión:** 18.0.1.0.2
