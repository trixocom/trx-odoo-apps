{
    'name': 'Trixo Sale Custom',
    'version': '18.0.1.0.0',
    'summary': 'Remove default "My Quotations" filter',
    'author': 'Trixocom',
    'depends': ['sale', 'account', 'l10n_ar_edi'],
    'data': [
        'views/sale_views.xml', 
        'views/account_move_fix.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'website': 'https://www.trixocom.com',
}
