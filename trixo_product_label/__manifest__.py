{
    'name': 'Trixo Product Label',
    'version': '18.0.1.0.10',
    'summary': 'Custom Product Labels for Trixocom',
    'description': """
        This module adds custom product label formats:
        - 2x7 with price
        - 4x7 with price
        - 4x12
        - 4x12 with price
        - 4xA4
        - ZPL Labels
    """,
    'author': 'Trixocom',
    'website': 'http://www.trixocom.com',
    'license': 'GPL-3',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'data': [
        'data/report_url_data.xml',
        'data/paperformat_data.xml',
        'wizard/product_label_layout_views.xml',
        'report/product_label_reports.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
