{
    'name': 'Crear Orden de Venta desde PdV',
    'version': '18.0.0.2',
    'category': 'Sales/Point of Sale',
    'summary': 'Crear orden de venta desde la pantalla de PdV y ver las órdenes creadas desde el PdV',
    'author': 'Warlock Technologies Pvt Ltd.',
    'description': '''
    ''',
    'website': 'http://warlocktechnologies.com',
    'support': 'support@warlocktechnologies.com',
    'depends': ['point_of_sale', 'sale_management','web','pos_sale'],
    "data": ['views/res_config_settings.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            "/wt_create_so_from_pos/static/src/app/control_buttons/control_buttons.xml",
            "/wt_create_so_from_pos/static/src/app/control_buttons/control_buttons.js",
            "/wt_create_so_from_pos/static/src/overrides/models/pos_store.js",
        ],
    },
    'images': ['static/images/screen_image.png'],
    'price': 00.00,
    'currency': "USD",
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
