# Guía de Instalación - Stock Packaging Invoice Report

## Versión 18.0.1.0.2 - Trixocom

### Pre-requisitos

**IMPORTANTE:** Este módulo requiere que `stock_packaging_report` esté instalado y configurado primero.

1. Odoo 18 Enterprise Edition
2. Módulo `stock_packaging_report` instalado
3. Módulo `account` (incluido por defecto)
4. Docker corriendo (si usas Docker)

---

## Instalación Rápida

```bash
# Desde el directorio del módulo
cd /Users/hector/claudecode/odoo18-dev/addons/stock_packaging_invoice_report
./install_module.sh
```

---

## Instalación Manual

### Paso 1: Verificar Dependencias

```bash
# Verificar que stock_packaging_report existe
ls /Users/hector/claudecode/odoo18-dev/addons/stock_packaging_report
```

Si no existe, instalar primero `stock_packaging_report`.

### Paso 2: Reiniciar Odoo

```bash
cd /Users/hector/claudecode/odoo18-dev
docker-compose restart web
```

O si no usas Docker:
```bash
sudo systemctl restart odoo
```

### Paso 3: Actualizar Lista de Módulos

1. Acceder a Odoo: http://localhost:8069
2. Activar modo desarrollador:
   - Ir a: Configuración → Activar modo desarrollador
3. Ir a: Aplicaciones
4. Clic en: Actualizar lista de aplicaciones (icono de actualización)
5. Confirmar

### Paso 4: Instalar stock_packaging_report (si no está instalado)

1. En Aplicaciones, buscar: "Stock Packaging Report"
2. Clic en: Instalar
3. Esperar a que complete

### Paso 5: Instalar Stock Packaging Invoice Report

1. En Aplicaciones, buscar: "Stock Packaging Invoice Report"
2. Clic en: Instalar
3. Esperar a que complete

---

## Configuración Post-Instalación

### 1. Configurar Nombre del Embalaje

```
Inventario → Configuración → Ajustes
```

1. Buscar: "Nombre del Embalaje para Stock"
2. Ingresar: Nombre del tipo de embalaje (ej: "Caja", "Bulto", "Pallet")
3. Guardar

**Nota:** Este nombre debe coincidir exactamente con el nombre en los embalajes del producto.

### 2. Configurar Embalajes en Productos

```
Inventario → Productos → [Seleccionar producto]
```

1. Ir a pestaña: **Inventario**
2. Sección: **Embalajes**
3. Clic en: **Agregar una línea**
4. Configurar:
   - **Nombre:** Mismo que configuraste en el sistema (ej: "Caja")
   - **Cantidad:** Unidades por embalaje (ej: 10)
   - **Código de barras:** (opcional)
5. Guardar

**Ejemplo:**
- Sistema configurado con: "Caja"
- Producto: Azúcar
- Embalaje: 
  - Nombre: "Caja"
  - Cantidad: 10 (10 unidades por caja)

---

## Verificación de Instalación

### Test 1: Verificar Campo en Vista

1. Ir a: Contabilidad → Clientes → Facturas
2. Crear nueva factura o abrir una existente
3. En las líneas de factura, buscar columna: "Cantidad de Embalaje"

✓ Si aparece la columna, el módulo está correctamente instalado.

### Test 2: Verificar Cálculo

1. Crear nueva factura
2. Seleccionar cliente
3. Agregar línea con producto configurado
4. Ingresar cantidad: 100
5. Verificar que "Cantidad de Embalaje" se calcula automáticamente

**Ejemplo de cálculo:**
- Producto: Azúcar (10 unidades por caja)
- Cantidad en línea: 100
- **Cantidad de Embalaje: 10 cajas**

### Test 3: Verificar Reporte PDF

1. Con una factura creada, clic en: Imprimir
2. Verificar que el PDF incluye:
   - Columna "Cantidad de Embalaje"
   - Total de embalajes al final

---

## Problemas Comunes

### Problema 1: El módulo no aparece en la lista

**Solución:**
```bash
# Verificar que el módulo está en addons
ls /Users/hector/claudecode/odoo18-dev/addons/stock_packaging_invoice_report

# Reiniciar Odoo
docker-compose restart web

# Actualizar lista de aplicaciones en Odoo
```

### Problema 2: Error de dependencia

**Error:** `Module stock_packaging_report not found`

**Solución:**
1. Instalar primero `stock_packaging_report`
2. Reiniciar Odoo
3. Intentar instalar nuevamente

### Problema 3: La columna no aparece

**Solución:**
1. Verificar que el módulo está instalado (no solo descargado)
2. Refrescar navegador (Ctrl + Shift + R)
3. Verificar modo desarrollador activado
4. Actualizar vista desde modo desarrollador

### Problema 4: El cálculo muestra 0.00

**Causas posibles:**
- No hay embalaje configurado en el producto
- El nombre del embalaje no coincide con el configurado en el sistema
- La cantidad en el embalaje es 0 o inválida
- El parámetro del sistema no está configurado

**Solución:**
1. Verificar configuración del sistema
2. Verificar embalaje del producto
3. Verificar que los nombres coincidan exactamente

### Problema 5: Error al instalar

**Revisar logs:**
```bash
docker-compose logs web | tail -100
```

O si no usas Docker:
```bash
sudo tail -f /var/log/odoo/odoo.log
```

---

## Desinstalación

Si necesitas desinstalar el módulo:

1. Ir a: Aplicaciones
2. Buscar: "Stock Packaging Invoice Report"
3. Clic en: Desinstalar
4. Confirmar

**Nota:** Esto no eliminará los datos, solo la funcionalidad.

---

## Actualización

Para actualizar el módulo a una nueva versión:

1. Reemplazar archivos del módulo
2. Reiniciar Odoo
3. Ir a: Aplicaciones
4. Buscar el módulo
5. Clic en: Actualizar

---

## Soporte

**Trixocom**
- Website: www.trixocom.com
- Documentación: README.md
- Changelog: CHANGELOG.md

---

## Checklist de Instalación

- [ ] Docker corriendo
- [ ] Odoo accesible en http://localhost:8069
- [ ] `stock_packaging_report` instalado
- [ ] Módulo copiado en addons
- [ ] Odoo reiniciado
- [ ] Lista de aplicaciones actualizada
- [ ] Módulo instalado sin errores
- [ ] Nombre de embalaje configurado en sistema
- [ ] Embalajes configurados en productos
- [ ] Campo visible en vista de factura
- [ ] Cálculo funcionando correctamente
- [ ] Reporte PDF muestra columna
- [ ] Sin errores en logs
