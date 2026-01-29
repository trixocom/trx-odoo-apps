{
    'name': 'Trixo Partner Security',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Restrict partner editing to specific group',
    'description': """
        Restricts the ability to edit (write) res.partner records to users who belong to the 'Editar Contactos' group.
        All internal users retain the ability to CREATE partners.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'contacts'],
    'data': [
        'security/security.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
