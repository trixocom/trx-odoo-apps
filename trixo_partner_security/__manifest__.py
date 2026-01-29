{
    'name': 'Trixo Partner Security',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Control partner creation/editing with separate groups',
    'description': """
        Restricts the ability to edit (write) and create res.partner records.
        - Group "Crear Contactos": Can create new partners.
        - Group "Editar Contactos": Can create AND edit partners.
        - No group: Read-only access.
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
