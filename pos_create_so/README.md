# POS - Crear Orden de Venta en lugar de Pago

## Descripción

Este módulo modifica el comportamiento del Punto de Venta (POS) de Odoo 18 para reemplazar el botón de "Pago" con un botón de "Crear Orden de Venta". 

**Caso de uso:** Cuando no se desea realizar el cobro en el POS, sino simplemente generar una orden de venta que será facturada posteriormente.

## Características

- ✅ Oculta el botón de pago estándar del POS
- ✅ Agrega un botón verde "Crear Orden de Venta"
- ✅ Crea automáticamente una orden de venta vinculada a la orden del POS
- ✅ Requiere que se seleccione un cliente antes de crear la orden
- ✅ Transfiere todos los productos, precios y descuentos a la orden de venta
- ✅ Mantiene la trazabilidad entre POS y órdenes de venta

## Requisitos

- Odoo 18.0 Community Edition
- Módulo `point_of_sale` (base)
- Módulo `sale` (base)

## Instalación

1. El módulo ya está copiado en: `/Users/hector/claudecode/odoo18-dev/addons/pos_create_so`

2. Reinicia el servidor Odoo:
   ```bash
   docker-compose restart
   ```

3. Actualiza la lista de aplicaciones en Odoo:
   - Ve a Aplicaciones
   - Haz clic en "Actualizar lista de aplicaciones"

4. Busca "POS - Crear Orden de Venta" e instálalo

## Estructura del Módulo

```
pos_create_so/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── pos_order.py
├── views/
│   └── pos_config_views.xml
└── static/
    └── src/
        ├── app/
        │   └── screens/
        │       └── payment_screen/
        │           ├── payment_screen.js
        │           └── payment_screen.xml
        └── css/
            └── payment_screen.css
```

## Uso

1. **Abrir sesión de POS:** Inicia sesión en tu punto de venta como lo harías normalmente

2. **Agregar productos:** Escanea o selecciona los productos que deseas agregar a la orden

3. **Seleccionar cliente:** **IMPORTANTE** - Debes seleccionar un cliente antes de continuar. El botón estará deshabilitado si no hay cliente seleccionado.

4. **Ir a pantalla de pago:** Haz clic en "Pago" para ir a la pantalla donde normalmente procesarías el pago

5. **Crear orden de venta:** En lugar del botón de "Validar", verás un botón verde "Crear Orden de Venta". Haz clic en él.

6. **Resultado:** Se creará automáticamente:
   - Una orden de venta en estado borrador
   - Vinculación entre la orden del POS y la orden de venta
   - La orden del POS se marcará como procesada

## Campos Transferidos a la Orden de Venta

- Cliente y direcciones de facturación/envío
- Lista de precios
- Productos con:
  - Cantidades
  - Precios unitarios
  - Descuentos
  - Impuestos
- Fecha de la orden
- Vendedor
- Notas

## Vistas Backend

El módulo agrega campos y filtros en las vistas del backend:

### Vista de Orden POS
- Campo "Orden de Venta" que muestra la SO vinculada
- Botón "Crear Orden de Venta" para creación manual si es necesario

### Filtros de Búsqueda
- "Con Orden de Venta": Filtra órdenes del POS que tienen SO
- "Sin Orden de Venta": Filtra órdenes del POS que no tienen SO

### Menú Adicional
- "POS con Órdenes de Venta": Acceso rápido a todas las órdenes con SO vinculadas

## Validaciones

El módulo incluye las siguientes validaciones:

1. **Cliente obligatorio:** No se puede crear la orden de venta sin cliente
2. **Productos en la orden:** Debe haber al menos un producto
3. **Evita duplicados:** No se puede crear una SO si ya existe una vinculada
4. **Cantidades positivas:** Solo se transfieren líneas con cantidad > 0

## Personalización

### Cambiar el color del botón

Edita el archivo `static/src/css/payment_screen.css`:

```css
.pos .payment-screen .create-sale-order-button {
    background-color: #28a745;  /* Cambia este valor */
}
```

### Agregar campos personalizados a la orden de venta

Modifica el método `_prepare_sale_order_values` en `models/pos_order.py`:

```python
def _prepare_sale_order_values(self):
    vals = super()._prepare_sale_order_values()
    vals.update({
        'mi_campo_personalizado': 'mi_valor',
    })
    return vals
```

## Solución de Problemas

### El botón no aparece
1. Verifica que el módulo esté instalado correctamente
2. Limpia la caché del navegador (Ctrl + Shift + R)
3. Revisa la consola del navegador en busca de errores JavaScript

### Error al crear la orden de venta
1. Verifica que el cliente tenga una lista de precios configurada
2. Verifica que todos los productos tengan precios configurados
3. Revisa los logs de Odoo para más detalles del error

### El botón aparece pero no pasa nada al hacer clic
1. Abre la consola del navegador (F12)
2. Busca errores en JavaScript
3. Verifica que los permisos del usuario incluyan crear órdenes de venta

## Compatibilidad

- ✅ Odoo 18.0 Community Edition
- ✅ Odoo 18.0 Enterprise Edition
- ❌ Versiones anteriores de Odoo (requiere adaptación)

## Soporte y Contribuciones

Si encuentras algún bug o tienes sugerencias de mejora:

1. Revisa la documentación de Odoo 18 para POS
2. Verifica el código fuente en GitHub: https://github.com/odoo/odoo/tree/18.0/addons/point_of_sale
3. Contacta al desarrollador del módulo

## Licencia

LGPL-3

## Créditos

**Desarrollado por:** Trixocom  
**Website:** www.trixocom.com

Desarrollado para sistemas POS que requieren generación de órdenes de venta sin proceso de pago inmediato.
