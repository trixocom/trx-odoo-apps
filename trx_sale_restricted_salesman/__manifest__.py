# -*- coding: utf-8 -*-
{
    "name": "Vendedor restringido",
    "version": "19.0.1.2.0",
    "summary": "Vendedores que solo ven sus propios clientes, pedidos y facturas, "
               "sin acceso a conversaciones ajenas, proveedores, costos ni listas de precios.",
    "description": """
Vendedor restringido
====================
Grupo **Vendedor restringido** para usuarios internos de ventas (vendedores
externos, distribuidores que levantan pedidos, etc.). Un usuario del grupo:

- ve solo los clientes que creó o que tiene asignados como vendedor
  (y sus contactos), más las empresas propias y los usuarios internos;
- ve solo sus pedidos de venta (y sus líneas) y sus facturas de venta;
- en Discuss ve solo los canales de los que es miembro (esto oculta, por
  ejemplo, las conversaciones de WhatsApp de la empresa);
- no ve proveedores de productos ni sus precios de compra;
- nunca ve el costo de los productos ni el costo/margen de los pedidos;
- no ve las listas de precios ni cómo están armadas: sus pedidos usan la
  lista fijada en su propia ficha (partner) y no la puede cambiar;
- en productos ve "Su precio" (el de su lista) en lugar del precio público.

Se implementa con reglas **globales condicionales**: para cualquier usuario
que no esté en el grupo el dominio es ``[(1, '=', 1)]``, así que al resto no
les cambia nada. Tienen que ser globales porque las reglas de grupo se combinan
con OR y no podrían achicar lo que ya dan "Ventas: solo sus documentos" u otras.
""",
    "author": "Trixocom",
    "website": "https://www.trixocom.com",
    "license": "LGPL-3",
    "category": "Sales/Sales",
    "depends": ["sale", "account", "mail", "product", "sale_margin"],
    "data": [
        "security/security.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
