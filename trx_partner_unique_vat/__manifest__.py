# -*- coding: utf-8 -*-
{
    'name': 'Contactos - Documento unico (Argentina)',
    'version': '19.0.1.1.0',
    'category': 'Contacts',
    'summary': 'Impide crear dos contactos con el mismo documento (CUIT, DNI, etc.) y redirige al original',
    'description': """Contactos - Documento unico (Argentina)
=======================================

Evita la duplicacion de contactos por documento de identidad. Cuando se intenta
crear o guardar un contacto cuyo documento ya existe en otro contacto, Odoo
muestra un **popup** con el aviso y un **boton** que lleva directamente al
contacto original.

Comportamiento
--------------
* Controla **todos los documentos reales**: CUIT, DNI, CUIL, Pasaporte, etc.
  Cada documento es unico por persona/entidad en Argentina.
* **Unica excepcion de tipo:** "Sin identificar / venta global diaria"
  (codigo AFIP ``99`` = Consumidor Final), que es normal que se repita.
* La comparacion se hace **dentro del mismo tipo de documento**, de modo que un
  DNI no colisiona con un CUIT que contenga los mismos digitos.
* Para CUIT se usa el valor compacto de la localizacion (``l10n_ar_vat``), por
  lo que ``20-12345678-9`` y ``20123456789`` son el mismo numero. Para el resto
  se normaliza quitando separadores (``12.345.678`` = ``12345678``).
* **Excepcion de jerarquia:** un contacto que cuelga de una empresa (tiene
  ``parent_id``) puede compartir el documento de su empresa. La unicidad se
  exige solo entre contactos de primer nivel (empresas / contactos
  independientes).
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
Si en la base ya existen documentos duplicados previos, el modulo no los rompe:
la restriccion se evalua al crear o guardar, no de forma retroactiva.
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
