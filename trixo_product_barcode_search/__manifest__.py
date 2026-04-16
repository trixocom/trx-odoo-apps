{
    'name': 'Búsqueda por Código de Barras (Predeterminada)',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Permite buscar productos por código de barras predeterminadamente en vistas tree y kanban',
    'description': """
    Este módulo asegura que al tipear en la caja de búsqueda predeterminada,
    se incluya el código de barras en los resultados junto con nombre y referencia interna.
    Esto permite escanear un código de barras en las vistas tree y kanban de productos sin necesidad de seleccionar la opción 'Código de Barras' manualmente.
    """,
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'changelog': '1.0.0 - Versión Inicial con soporte Odoo 18',
}
