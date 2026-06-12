# -*- coding: utf-8 -*-
{
    'name': 'TRX HTML Editor Align Fix',
    'version': '19.0.1.0.0',
    'summary': 'Guarda AlignPlugin.updateAlignmentParams contra this.alignment undefined',
    'description': '''
Corrige el error de cliente intermitente de Odoo 19:

    TypeError: Cannot set properties of undefined (setting 'displayName')
        at AlignPlugin.updateAlignmentParams

El handler de selectionchange del editor html es un listener GLOBAL del
documento (SelectionPlugin.addGlobalDomListener). Puede dispararse mientras una
instancia del editor todavia se inicializa (antes de setup(), donde se crea
this.alignment = reactive({...})) o durante su teardown. En ese instante
this.alignment es undefined y la asignacion this.alignment.displayName lanza la
excepcion. Mas frecuente en navegadores que disparan selectionchange de forma
sincrona durante la creacion del editor.

Odoo core (19.0 y master) no tiene guarda. Este modulo parchea
AlignPlugin.prototype.updateAlignmentParams para no hacer nada cuando
this.alignment aun no existe. Cambio aditivo, reversible, sin tocar core.
''',
    'author': 'Trixocom',
    'website': 'https://www.trixocom.com',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'depends': ['html_editor'],
    'assets': {
        'web.assets_backend': [
            'trx_html_editor_align_fix/static/src/js/align_plugin_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
