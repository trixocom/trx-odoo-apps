# Part of Trixocom. Multi-connector WhatsApp for Odoo Community.
{
    'name': "Trixocom WhatsApp (multi-conector)",
    'version': "19.0.1.2.5",
    'category': "Productivity/WhatsApp",
    'summary': "Conecta WhatsApp con la plataforma de mensajería de Odoo (Meta Cloud API y whatsmeow)",
    'description': """
Trixocom WhatsApp multi-conector
================================
Integra WhatsApp con Discuss / mensajería de Odoo Community mediante una capa de
proveedores intercambiables:

* **Meta Cloud API** — canal oficial de WhatsApp Business (con plantillas).
* **whatsmeow** — conexión directa por QR vía un sidecar REST (WhatsApp Web multidevice).

Desarrollo propio de Trixocom para Odoo Community.
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
        'views/whatsapp_call_views.xml',
        'views/whatsapp_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trixo_whatsapp/static/src/whatsapp_call_service.js',
        ],
    },
    'application': True,
    'installable': True,
}
