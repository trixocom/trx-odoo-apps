{
    'name': 'POS - Precio en tarjeta y unitario por linea',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Muestra el precio en la tarjeta de producto del POS y el '
               'precio unitario en cada linea del ticket (paridad con Odoo 16)',
    'description': """
Reponer comportamiento visual del POS de Odoo 16 sobre Odoo 19:

* Precio de venta visible en cada tarjeta de producto (ProductCard), usando el
  getter estandar product.template.displayPriceUnit, que respeta la config de
  impuestos del POS (iface_tax_included).
* Precio unitario "X / unidad" visible en cada linea del ticket aunque la
  cantidad sea 1 (en Odoo 19 el core lo oculta salvo cantidad != 1 o precio
  editado a mano).

Sin copia de codigo de terceros. Override de plantilla + patch JS.
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'trx_pos_price_display/static/src/product_card_price.js',
            'trx_pos_price_display/static/src/product_card_price.xml',
            'trx_pos_price_display/static/src/orderline_unit_price.js',
            'trx_pos_price_display/static/src/style.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
