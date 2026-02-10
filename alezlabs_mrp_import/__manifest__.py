{
    'name': 'Alezlabs MRP Formulas',
    'version': '18.0.1.0.0',
    'summary': 'Gestión de Fórmulas Cosméticas e Importación de LDM',
    'author': 'Antigravity',
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'wizard/import_bom_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
