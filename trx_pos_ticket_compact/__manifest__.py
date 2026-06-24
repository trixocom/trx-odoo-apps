{
    'name': 'POS - Ticket compacto + código interno en línea',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Reduce 25% la letra del panel de pedido y del ticket, y muestra el '
               'código interno (default_code) en la línea del pedido y en el ticket',
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
