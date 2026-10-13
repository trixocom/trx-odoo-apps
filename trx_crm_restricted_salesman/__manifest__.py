# -*- coding: utf-8 -*-
{
    'name': 'Trixocom - Vendedor restringido (solo CRM)',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Vendedores que sólo ven el CRM: sus leads, sus clientes, sus '
               'cotizaciones y los productos/listas de precios habilitados',
    'description': """
Vendedor restringido (solo CRM)
===============================

Agrega el grupo **Vendedor restringido (solo CRM)** (Ventas). Un usuario con
este grupo:

* Sólo ve la app **CRM** en el menú principal (no ve ningún otro ícono de app,
  ni Conversaciones, Calendario, Contactos, WhatsApp, Teléfono, etc.).
* Ve y crea **sólo sus propios leads/oportunidades** (no los sin asignar ni los
  de otros vendedores), y sus propias cotizaciones/pedidos.
* **Contactos**: sólo los creados por él, los que tienen a él como vendedor
  asignado, los de sus oportunidades y cotizaciones (y sus contactos hijos),
  más los usuarios internos y las compañías propias (necesarios para que el
  sistema funcione).
* **Productos y listas de precios**: sólo los que tienen tildado
  "Visible para vendedores restringidos" (por defecto ninguno).
* **Costos**: no ve el costo del producto ni los campos de costo de
  reposición / precio planificado.
* **WhatsApp**: puede enviar desde el chatter de SUS documentos (lead,
  cotización, cliente) y ve las respuestas que vuelven a ese chatter; no tiene
  acceso al cliente WhatsApp Web, ni a los chats/historial/contactos de la
  cuenta, ni a la configuración del módulo.
* No ve facturas ajenas, transacciones de pago, eventos de calendario de otros,
  proyectos/tareas que no sigue, tableros, canales de Conversaciones de los que
  no es miembro, cuentas bancarias, proveedores de productos, llamadas VoIP de
  otros ni el directorio de empleados.

Las restricciones son reglas de registro GLOBALES condicionadas al grupo, así
que se suman (AND) a cualquier otro permiso que el usuario tenga.
    """,
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale_crm',
        'project',
        'hr',
        'spreadsheet_dashboard',
        'trixo_whatsapp',
        'product_replenishment_cost',
        'product_planned_price',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_rule_data.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
