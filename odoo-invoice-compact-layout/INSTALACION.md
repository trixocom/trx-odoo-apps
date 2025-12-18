# GUÍA DE INSTALACIÓN - Invoice Compact Layout Odoo 18
## Paso a Paso para Instalar el Módulo

### 📋 Prerequisitos
- Odoo 18 instalado y funcionando
- Acceso SSH al servidor o acceso a Docker/Portainer
- Permisos de administrador en Odoo

---

## 🚀 MÉTODO 1: Instalación con Docker/Portainer (RECOMENDADO)

### Paso 1: Clonar el repositorio
```bash
cd /ruta/de/tus/addons/
git clone https://github.com/trixocom/odoo-invoice-compact-layout.git odoo_invoice_compact
```

### Paso 2: Verificar permisos
```bash
chown -R odoo:odoo odoo_invoice_compact/
chmod -R 755 odoo_invoice_compact/
```

### Paso 3: Reiniciar contenedor de Odoo
Si usas Docker Compose:
```bash
docker-compose restart odoo
```

Si usas Portainer:
1. Ve a tu stack de Odoo
2. Click en "Restart" en el contenedor de Odoo

### Paso 4: Activar modo desarrollador en Odoo
1. Inicia sesión en Odoo como administrador
2. Ve a **Configuración** → **Activar el modo desarrollador**

### Paso 5: Actualizar lista de aplicaciones
1. Ve a **Aplicaciones**
2. Click en el menú de tres puntos (⋮)
3. Click en **Actualizar Lista de Aplicaciones**
4. Click en **Actualizar**

### Paso 6: Instalar el módulo
1. En **Aplicaciones**, busca: `Invoice Compact`
2. Deberías ver "Invoice Compact Layout"
3. Click en **Instalar**

### Paso 7: Verificar instalación
1. Ve a **Contabilidad** → **Clientes** → **Facturas**
2. Abre cualquier factura
3. Click en **Imprimir** → **Factura**
4. El espaciado debería estar reducido automáticamente

---

## 🖥️ MÉTODO 2: Instalación Manual (Sin Docker)

### Paso 1: Descargar el módulo
```bash
cd /opt/odoo/addons/
git clone https://github.com/trixocom/odoo-invoice-compact-layout.git odoo_invoice_compact
```

### Paso 2: Permisos
```bash
sudo chown -R odoo:odoo odoo_invoice_compact/
sudo chmod -R 755 odoo_invoice_compact/
```

### Paso 3: Agregar ruta en configuración de Odoo
Edita tu archivo de configuración (usualmente `/etc/odoo/odoo.conf`):
```ini
[options]
addons_path = /opt/odoo/addons,/opt/odoo/custom-addons,/opt/odoo/addons/odoo_invoice_compact
```

### Paso 4: Reiniciar servicio Odoo
```bash
sudo systemctl restart odoo
```

### Paso 5: Seguir pasos 4-7 del Método 1

---

## 🔧 MÉTODO 3: Instalación desde ZIP

### Paso 1: Descargar
```bash
wget https://github.com/trixocom/odoo-invoice-compact-layout/archive/refs/heads/main.zip
unzip main.zip
mv odoo-invoice-compact-layout-main odoo_invoice_compact
```

### Paso 2: Copiar a addons
```bash
cp -r odoo_invoice_compact /ruta/a/tus/addons/
```

### Paso 3: Seguir pasos 2-7 del Método 1 o 2

---

## ✅ VERIFICACIÓN

Después de instalar, verifica que el módulo funciona correctamente:

1. **Imprime una factura de prueba**
   - El espacio entre "Inicio de actividades" y los datos del cliente debe ser mínimo (aproximadamente 2mm)

2. **Verifica en el inspector de elementos** (F12 en el navegador)
   - La clase `invoice-compact-layout` debe estar presente en el div principal
   - Los estilos SCSS deben estar cargados

3. **Revisa el log de Odoo**
   ```bash
   tail -f /var/log/odoo/odoo-server.log
   ```
   No deberían aparecer errores relacionados con el módulo

---

## 🎨 PERSONALIZACIÓN

### Ajustar espaciado
Edita el archivo: `odoo_invoice_compact/static/src/scss/report_invoice_compact.scss`

Cambia estas variables según tus necesidades:
```scss
$compact-padding: 1mm;    // Espaciado interno (aumenta para más espacio)
$compact-margin: 2mm;     // Margen entre secciones (aumenta para más espacio)
$minimal-gap: 0mm;        // Espacio mínimo (aumenta para más espacio)
```

Después de modificar, regenera los assets:
```bash
./odoo-bin -c /etc/odoo/odoo.conf -d tu_base_de_datos -u odoo_invoice_compact
```

O desde la interfaz web:
1. Modo desarrollador activado
2. Ve a **Configuración** → **Técnico** → **Interfaz de usuario** → **Vistas**
3. Busca vistas relacionadas con `odoo_invoice_compact`
4. Click en **Regenerar Assets**

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### El módulo no aparece en la lista de aplicaciones
```bash
# Verifica que el módulo esté en la ruta correcta
ls -la /ruta/a/addons/odoo_invoice_compact/

# Verifica permisos
ls -l /ruta/a/addons/odoo_invoice_compact/__manifest__.py

# Revisa el log
tail -f /var/log/odoo/odoo-server.log
```

### Los estilos no se aplican
```bash
# Regenera los assets
./odoo-bin -c /etc/odoo/odoo.conf -d nombre_bd -u odoo_invoice_compact

# O borra la caché del navegador (Ctrl + Shift + R)
```

### Error al instalar
```bash
# Verifica dependencias
# El módulo requiere el módulo 'account' instalado

# Verifica la versión de Odoo
./odoo-bin --version
# Debe ser 18.0
```

---

## 📞 SOPORTE

Si tienes problemas:
1. Revisa el log de Odoo: `/var/log/odoo/odoo-server.log`
2. Verifica que el módulo 'account' esté instalado
3. Abre un issue en: https://github.com/trixocom/odoo-invoice-compact-layout/issues

---

## 📝 NOTAS IMPORTANTES

- ⚠️ **Backup**: Siempre haz un backup de tu base de datos antes de instalar módulos nuevos
- 🔄 **Actualización**: Para actualizar el módulo, haz `git pull` y luego actualiza el módulo desde Odoo
- ❌ **Desinstalación**: Para desinstalar, ve a Aplicaciones → Invoice Compact Layout → Desinstalar

---

## 🎯 RESULTADO ESPERADO

**ANTES:**
```
[Logo Empresa]
Inicio de actividades: XX/XX/XXXX


        <--- ESPACIO GRANDE --->


Cliente: Juan Pérez
...
```

**DESPUÉS:**
```
[Logo Empresa]
Inicio de actividades: XX/XX/XXXX
Cliente: Juan Pérez  <--- ESPACIO MÍNIMO
...
```

El espacio se reduce de aproximadamente 20-30mm a solo 2-3mm.
