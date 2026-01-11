{
    'name': 'Trixo Shipping Label',
    'version': '19.0.1.0.8',
    'summary': 'Generates a custom shipping label for Stock Picking',
    'description': """
        This module adds a custom Shipping Label report for Stock Pickings.
        It uses a specific layout with:
        - Recipient Address
        - Sender Address
        - Transport Information
        - Weight and Package Count
    """,
    'author': 'Antigravity',
    'category': 'Stock',
    'depends': ['stock', 'delivery', 'l10n_ar_stock'],
    'data': [
        'views/res_partner_views.xml',
        'data/paper_format.xml',
        'reports/shipping_label_report.xml',
        'reports/stock_picking_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
