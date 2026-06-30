# Part of Trixocom. Multi-connector WhatsApp for Odoo Community.
{
    'name': "Trixocom WhatsApp (multi-conector)",
    'version': "19.0.1.0.5",
    'category': "Productivity/WhatsApp",
    'summary': "Conecta WhatsApp con la plataforma de mensajería de Odoo (Meta Cloud API y whatsmeow)",
    'description': """
Trixocom WhatsApp multi-conector
================================
Integra WhatsApp con Discuss / mensajería de Odoo Community mediante una capa de
proveedores intercambiables:

* **Meta Cloud API** — canal oficial de WhatsApp Business (con plantillas).
* **whatsmeow** — conexión directa por QR vía un sidecar REST (WhatsApp Web multidevice).

Inspirado en la interfaz del módulo Enterprise de Odoo, reimplementado para Community.
""",
    'author': "Trixocom",
    'website': "https://www.trixocom.com",
    'license': "LGPL-3",
    'depends': [
        'mail',
        'phone_validation',
    ],
    'data': [
        'security/whatsapp_security.xml',
        'security/ir.model.access.csv',
        'views/whatsapp_account_views.xml',
        'views/whatsapp_message_views.xml',
        'views/whatsapp_menus.xml',
    ],
    'application': True,
    'installable': True,
}
