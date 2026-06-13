# -*- coding: utf-8 -*-
{
    'name': 'Contactos - CUIT unico (Argentina)',
    'version': '19.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Impide crear dos contactos con el mismo CUIT y redirige al original',
    'description': """Contactos - CUIT unico (Argentina)
==================================

Evita la duplicacion de contactos por CUIT. Cuando se intenta crear o guardar
un contacto cuyo CUIT ya existe en otro contacto, Odoo muestra un **popup** con
el aviso y un **boton** que lleva directamente al contacto original.

Comportamiento
--------------
* El control aplica solo a documentos de tipo **CUIT** (codigo AFIP ``80``).
  Para DNI, CF u otros documentos NO se exige unicidad, ya que es normal que se
  repitan (por ejemplo varios "Consumidor Final").
* La comparacion usa el CUIT compacto de la localizacion (``l10n_ar_vat``), por
  lo que ``20-12345678-9`` y ``20123456789`` se consideran el mismo numero.
* **Excepcion:** un contacto que cuelga de una empresa (tiene ``parent_id``)
  puede compartir el CUIT de su empresa. La unicidad se exige solo entre
  contactos de primer nivel (empresas / contactos independientes).
* Considera tambien contactos archivados (avisa indicando que lo esta).
* Se respeta el alcance por compania (``company_id``).

Tecnico
-------
* ``@api.constrains`` sobre ``res.partner`` (campos ``vat``, ``parent_id``,
  ``l10n_latam_identification_type_id``, ``company_id``).
* El popup con boton se implementa con ``RedirectWarning`` apuntando al
  formulario del contacto original.
* Para procesos masivos (migraciones / importaciones) el control se puede
  saltear pasando el contexto ``trx_skip_unique_vat=True``.

Nota
----
Si en la base ya existen CUIT duplicados previos, el modulo no los rompe: la
restriccion se evalua al crear o guardar, no de forma retroactiva.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'l10n_ar',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
