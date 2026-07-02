{
    'name': 'POS - Ticket compacto + codigo interno en linea',
    'version': '19.0.1.1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Reduce 25% la letra del ticket y del panel de pedido, agranda y '
               'pone en negrita la linea del pedido (tamano tarjeta), y muestra el '
               'codigo interno (default_code) en la linea del pedido y en el ticket',
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'trx_pos_ticket_compact/static/src/orderline_ref.js',
            'trx_pos_ticket_compact/static/src/compact.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
