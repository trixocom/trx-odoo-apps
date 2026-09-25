# trx_sale_restricted_salesman (Odoo 19)

Grupo **Vendedor restringido** para usuarios internos de ventas. Un usuario del grupo:

| Qué | Ve |
|---|---|
| Contactos | Los que creó o tiene asignados como vendedor, sus contactos hijos, las empresas propias y los usuarios internos |
| Pedidos y líneas | Solo los que tiene como vendedor o creó |
| Facturas | Solo facturas y notas de crédito de venta suyas |
| Discuss / WhatsApp | Solo los canales de los que es miembro |
| Proveedores de productos | Nada |
| Costo de productos / costo y margen del pedido | Nunca (los cálculos lo leen como sistema) |
| Precio en productos | "Su precio" (el de su lista) en lugar del precio público, en ficha, lista y tarjetas |
| Listas de precios | Solo la fijada en su propia ficha de contacto; no ve las reglas ni puede cambiar la lista del pedido |

Reglas **globales condicionales**: para los usuarios fuera del grupo el dominio es `[(1, '=', 1)]`; no cambia nada.
Se usan globales porque las reglas de grupo se combinan con OR y no podrían restringir lo que ya dan otros grupos.

Uso: en la ficha de contacto del vendedor fijar la lista de precios que usa; agregar el usuario (interno, Ventas: "Solo sus documentos") al grupo *Vendedor restringido*.
Rollback: sacarlo del grupo.

Autor: Trixocom · LGPL-3
