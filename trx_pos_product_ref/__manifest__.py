{
    'name': 'POS - Referencia interna en tarjeta de producto',
    'version': '19.0.1.2.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Muestra el codigo interno (default_code) junto al nombre en la tarjeta de producto del POS',
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'trx_pos_product_ref/static/src/product_screen.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
