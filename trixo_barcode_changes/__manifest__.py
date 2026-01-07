{
    'name': 'Trixo Barcode Adjustments',
    'version': '18.0.1.0.0',
    'summary': 'Small adjustments to Barcode App behavior for Trixo',
    'description': """
        This module overrides the default sorting of Stock Pickings in the Barcode App.
        It forces 'Creation Date Descending' so that new pickings appear first,
        solving issues where limits hide new records when many old ones exist.
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'category': 'Inventory/Barcode',
    'depends': ['stock', 'stock_barcode'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'license': 'GPL-3',
}
