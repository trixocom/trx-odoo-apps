{
    'name': 'Trixo Shipping Label',
    'version': '19.0.2.1.0',
    'summary': 'Generates a custom shipping label for Stock Picking',
    'description': '\n        This module adds a custom Shipping Label report for Stock Pickings.\n        It uses a specific layout with:\n        - Recipient Address\n        - Sender Address\n        - Transport Information\n        - Weight and Package Count\n    ',
    'author': 'Trixocom',
    'category': 'Stock',
    'depends': ['stock', 'delivery', 'l10n_ar_stock'],
    'data': ['views/res_partner_views.xml', 'data/paper_format.xml', 'reports/shipping_label_report.xml', 'reports/stock_picking_report.xml'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'website': 'https://www.trixocom.com',
}
