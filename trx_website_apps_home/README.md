# TRX Website Apps Home

Cambia el comportamiento del boton de apps (grilla) que aparece en el frontend
del sitio web para usuarios internos.

- **Antes (Odoo 19 estandar):** el boton abre un menu desplegable con la lista
  de aplicaciones (`data-bs-toggle="dropdown"`).
- **Despues (con este modulo):** el boton lleva directamente a `/odoo`, el home
  del backend con los iconos de las apps.

## Como funciona

Hereda `website.layout` y, sobre el boton `o_frontend_to_backend_apps_btn`:

- quita el atributo `data-bs-toggle` y fija `href="/odoo"`;
- elimina el `div.o_frontend_to_backend_apps_menu` que queda sin uso.

Es un cambio puramente declarativo (QWeb), aditivo y reversible. No modifica
codigo fuente de Odoo. Al desinstalar el modulo se restaura el comportamiento
original.

## Dependencias

- `website`

## Compatibilidad

- Odoo 19.0 Community

Autor: Trixocom — https://www.trixocom.com — LGPL-3
