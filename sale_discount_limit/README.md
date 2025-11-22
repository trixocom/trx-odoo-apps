# Sale Discount Limit

## Descripción

Módulo para Odoo 18 que permite controlar los descuentos máximos que cada usuario puede aplicar en órdenes de venta.

## Características

- **Configuración por Usuario**: Asigna un descuento máximo permitido para cada usuario del sistema
- **Validación Automática**: Verifica que el descuento aplicado no supere el límite asignado
- **Mensajes Amigables**: Muestra mensajes claros al usuario indicando su límite de descuento
- **Validación en Tiempo Real**: Alerta al usuario mientras edita el descuento
- **Validación al Guardar**: Impide guardar líneas con descuentos superiores al permitido

## Instalación

1. Copiar el módulo en el directorio de addons de Odoo
2. Actualizar la lista de módulos
3. Instalar el módulo "Sale Discount Limit"

## Configuración

1. Ir a **Ventas > Configuración > Descuentos por Usuario**
2. Seleccionar un usuario
3. En la pestaña "Preferencias", sección "Control de Descuentos en Ventas":
   - Establecer el **Descuento Máximo (%)** permitido para ese usuario
4. Guardar los cambios

## Uso

Cuando un usuario intenta aplicar un descuento en una línea de orden de venta:

1. Si el descuento es menor o igual al máximo permitido: se aplica normalmente
2. Si el descuento es mayor al máximo permitido: 
   - Se muestra una advertencia en tiempo real
   - Si intenta guardar, se muestra un error bloqueante con el mensaje:
     > "No puede aplicar un descuento de X%. Su descuento máximo permitido es de Y%."

## Ejemplo

Si un usuario tiene configurado un descuento máximo del 10%:
- ✅ Puede aplicar descuentos del 0% al 10%
- ❌ No puede aplicar descuentos superiores al 10%

## Autor

Trixocom

## Licencia

GPL-3
