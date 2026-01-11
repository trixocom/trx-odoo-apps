# Sale Default Packaging

Módulo para Odoo 19 que establece automáticamente el embalaje por defecto en las líneas de venta, basándose en la configuración de Stock Packaging Report.

## 🎯 Características

- ✅ **Embalaje automático**: Establece el embalaje configurado en Stock Packaging Report al seleccionar un producto
- ✅ **Cantidad por defecto**: Define automáticamente 1 embalaje por defecto
- ✅ **Cálculo automático**: Calcula las unidades de producto basándose en la cantidad de embalajes
- ✅ **Sincronización bidireccional**: Los cambios en cantidades se sincronizan automáticamente
- ✅ **Interfaz intuitiva**: Campos claros y fáciles de usar en las líneas de venta

## 📋 Dependencias

- `sale`: Módulo de ventas de Odoo
- `stock`: Módulo de inventario de Odoo
- `product`: Módulo de productos de Odoo
- `stock_packaging_report`: [Módulo de Stock Packaging Report](https://github.com/trixocom/odoo_stock_packaging_report)

## 🚀 Instalación

1. **Clonar el repositorio**:
```bash
cd /mnt/extra-addons
git clone https://github.com/trixocom/sale_default_packaging.git
```

2. **Reiniciar Odoo**:
```bash
sudo systemctl restart odoo
```

3. **Instalar el módulo**:
   - Ir a Aplicaciones
   - Actualizar lista de aplicaciones
   - Buscar "Sale Default Packaging"
   - Clic en Instalar

## ⚙️ Configuración

### 1. Configurar Stock Packaging Report

Primero, debes tener instalado y configurado el módulo `stock_packaging_report`:

- Ir a **Inventario > Configuración > Ajustes**
- Buscar la sección **"Nombre del Embalaje para Stock"**
- Ingresar el nombre exacto del tipo de embalaje (ejemplo: `"Caja"`, `"Bulto"`, `"Pallet"`)
- Guardar

### 2. Configurar Embalajes en Productos

Para cada producto:

- Abrir el producto
- Ir a la pestaña **"Inventario"**
- En la sección **"Embalajes"**, agregar o editar:
  - **Nombre**: Debe coincidir exactamente con el configurado en Ajustes (ej: `"Caja"`)
  - **Cantidad**: Define cuántas unidades contiene ese embalaje (ej: `10`)

## 📊 Uso

### En las Líneas de Venta

Una vez configurado, al crear una orden de venta:

1. **Seleccionar un producto**: El sistema automáticamente:
   - Busca el embalaje configurado para ese producto
   - Establece 1 embalaje por defecto
   - Calcula las unidades de producto (1 embalaje × unidades por embalaje)

2. **Modificar la cantidad de embalajes**:
   - Cambiar el campo "Cant. Embalajes"
   - Las unidades de producto se actualizan automáticamente

3. **Modificar las unidades de producto**:
   - Cambiar el campo "Cantidad"
   - La cantidad de embalajes se recalcula automáticamente

### Ejemplo

**Configuración**:
- Nombre del embalaje: `"Caja"`
- Producto: Azúcar Ledesma X 1 KG
- Embalaje configurado:
  - Nombre: `"Caja"`
  - Cantidad: `10` unidades por caja

**Comportamiento en la venta**:
1. Seleccionas el producto "Azúcar Ledesma X 1 KG"
2. El sistema automáticamente establece:
   - Embalaje: `Caja`
   - Cant. Embalajes: `1.0`
   - Cantidad: `10.0` unidades

3. Si cambias Cant. Embalajes a `5.0`:
   - Cantidad se actualiza a: `50.0` unidades

4. Si cambias Cantidad a `25.0` unidades:
   - Cant. Embalajes se actualiza a: `2.5`

## 🔧 Campos Añadidos

### En sale.order.line

- **product_packaging_id** (Many2one): Embalaje del producto
- **product_packaging_qty** (Float): Cantidad de embalajes

## 📝 Fórmulas

```
Unidades de Producto = Cantidad de Embalajes × Unidades por Embalaje

Cantidad de Embalajes = Unidades de Producto ÷ Unidades por Embalaje
```

## ⚠️ Consideraciones Importantes

1. **Nombre exacto**: El nombre del embalaje en la configuración debe coincidir EXACTAMENTE con el nombre del packaging del producto (es case-sensitive).

2. **Sin embalaje configurado**: Si un producto no tiene el embalaje configurado, el sistema no establecerá valores por defecto.

3. **Cantidad readonly**: Cuando se selecciona un embalaje, la cantidad de producto se vuelve de solo lectura para evitar inconsistencias. Para cambiar la cantidad, modifica la cantidad de embalajes.

## 🐛 Solución de Problemas

### El embalaje no se establece automáticamente

**Causa**: El producto no tiene un packaging configurado con el nombre exacto.

**Solución**:
- Verificar que el nombre del embalaje en Ajustes sea exacto
- Ir al producto > pestaña Inventario > Embalajes
- Crear/editar un packaging con el nombre exacto
- Refrescar la página

### Las cantidades no se calculan correctamente

**Verificar**:
- El campo `qty` del packaging está correctamente configurado
- La cantidad de embalajes es un número válido
- Refrescar el navegador

## 📅 Changelog

### v1.1.2 (2025-11-08)
- 🔧 Corrección de nombre de dependencia: stock_packaging_report

### v1.1.1 (2025-11-08)
- 🔧 Corrección de xpath en vistas XML para Odoo 19

### v1.1.0 (2025-11-08)
- ✨ Refactorización completa del modelo
- 🔧 Mejora en el cálculo de cantidades
- 🔄 Sincronización bidireccional entre cantidades
- 🎨 Vista mejorada con campos más intuitivos
- 🔗 Mejor integración con stock_packaging_report
- 📚 Documentación completa

### v1.0.0
- ✨ Versión inicial
- ✨ Embalaje por defecto en líneas de venta
- ✨ Cálculo básico de cantidades

## 📄 Licencia

LGPL-3

## 👥 Autor

**Trixocom**
- GitHub: [@trixocom](https://github.com/trixocom)
- Web: [https://trixocom.com](https://trixocom.com)

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🆘 Soporte

Si encuentras algún problema o tienes alguna pregunta:
- 🐛 Reporta bugs en [GitHub Issues](https://github.com/trixocom/sale_default_packaging/issues)
- 💬 Preguntas en [GitHub Discussions](https://github.com/trixocom/sale_default_packaging/discussions)

---

⭐ Si este módulo te resulta útil, ¡no olvides darle una estrella en GitHub!

**Última actualización**: Noviembre 2025
