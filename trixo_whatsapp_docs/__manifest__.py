# Part of Trixocom.
{
    'name': "Trixocom WhatsApp — Documentos",
    'version': "19.0.1.0.0",
    'category': "Productivity/WhatsApp",
    'summary': "Enviar documentos (venta, compra, factura, remito) por WhatsApp al contacto",
    'description': """
Agrega un botón **WhatsApp** en pedidos de venta, pedidos de compra, facturas y
remitos para enviarle al contacto el PDF del documento por WhatsApp, con un mensaje
opcional. Reutiliza la mensajería de `trixo_whatsapp` (el envío queda registrado en
el canal de Discuss del contacto).
""",
    'author': "Trixocom",
    'website': "https://www.trixocom.com",
    'license': "LGPL-3",
    'depends': ['trixo_whatsapp', 'sale', 'purchase', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/whatsapp_compose_views.xml',
        'views/document_buttons.xml',
    ],
    'installable': True,
}
