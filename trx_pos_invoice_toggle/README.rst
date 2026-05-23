============================================
Trixocom POS - Toggle Factura en Primera Pantalla
============================================

.. |badge_license| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html

|badge_license|

Qué hace
========

Saca el botón **Invoice / Recibo-Factura** de la *Payment Screen* del Punto de
Venta y lo coloca, en formato compacto (sólo icono + check de estado), en la
fila de *control buttons* de la pantalla principal (*Product Screen*).

Por qué
=======

El operador del POS necesita decidir *antes* de cobrar si la operación se
emite como factura fiscal o sólo como recibo. Tenerlo en la primera pantalla
acelera el flujo y evita el "lo dejé sin facturar" que se descubre recién en
el momento del pago.

Cómo funciona
=============

* Reutiliza el flujo existente: ``order.setToInvoice(true/false)``.
* Respeta ``pos.config.canInvoice`` (botón en opacidad reducida si el POS no
  tiene un diario de facturación configurado).
* Bloquea el botón cuando la orden actual refunda una orden previamente
  facturada (mismo comportamiento que el original).

Limitaciones conocidas
======================

* Sólo se ve la versión "siempre visible" del control bar; dentro del popup
  "Más acciones" no se duplica para no contaminar esa lista.

Autor
=====

* Trixocom
