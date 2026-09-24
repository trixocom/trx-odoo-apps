# -*- coding: utf-8 -*-
{
    "name": "Distribuidores en la tienda web",
    "version": "19.0.1.0.1",
    "summary": "Portal de distribuidores: catálogo completo, stock visible, "
               "pedido sin stock, retiro y pago en el local, y aviso de cada "
               "pedido por push y WhatsApp.",
    "description": """
Distribuidores en la tienda web
===============================
- Grupo *Distribuidor (portal)* para usuarios portal.
- El distribuidor ve también los productos no publicados (regla desactivable).
- Ve siempre la cantidad en stock y puede pedir aunque no haya stock.
- Retiro y pago en el local (Click & Collect) solo para distribuidores.
- Cada pedido web de un distribuidor avisa a todos los usuarios internos
  (notificación + push) y por WhatsApp a los destinos configurados.
""",
    "author": "Trixocom",
    "website": "https://www.trixocom.com",
    "license": "LGPL-3",
    "category": "Website/Website",
    "depends": ["website_sale_stock", "website_sale_collect", "mail"],
    "data": [
        "security/groups.xml",
        "security/ir_rules.xml",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}
