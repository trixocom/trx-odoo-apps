# Guía de Instalación - POS Crear Orden de Venta

## Versión 18.0.1.0.2 - Trixocom

### Instalación rápida

```bash
# Desde el directorio raíz del proyecto odoo18-dev
./addons/pos_create_so/install_module.sh
```

### Instalación manual

1. **Reiniciar Odoo**
```bash
cd /Users/hector/claudecode/odoo18-dev
docker-compose restart
```

2. **Actualizar lista de módulos**
- Acceder a Odoo: http://localhost:8069
- Ir a: Aplicaciones
- Clic en: Actualizar lista de aplicaciones (icono de actualización)

3. **Instalar el módulo**
- Buscar: "POS - Crear Orden de Venta"
- Clic en: Instalar

### Verificación

1. Abrir una sesión POS
2. Agregar productos
3. Seleccionar cliente
4. Ir a pantalla de pago
5. Verificar botón verde "Crear Orden de Venta"

### Desinstalación

Si necesitas desinstalar:

```bash
# En Odoo, ir a Aplicaciones
# Buscar "POS - Crear Orden de Venta"
# Clic en Desinstalar
```

### Problemas comunes

**El módulo no aparece en la lista**
- Verificar que el directorio esté en: `/Users/hector/claudecode/odoo18-dev/addons/`
- Reiniciar el contenedor Docker
- Actualizar lista de aplicaciones

**Error al instalar**
- Verificar logs: `docker-compose logs -f`
- Verificar dependencias: `point_of_sale` y `sale` deben estar instalados

**El botón no aparece en POS**
- Limpiar caché del navegador (Ctrl + Shift + R)
- Verificar consola JavaScript (F12)
- Verificar que la sesión POS esté abierta correctamente
