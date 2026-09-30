# -*- coding: utf-8 -*-
{
    'name': 'Ventas AR - IVA coherente con la posicion fiscal',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Recalcula los impuestos del pedido al cambiar la posicion '
               'fiscal y no deja validar facturas fiscales con IVA 0%',
    'description': """
Ventas AR - IVA coherente con la posicion fiscal
================================================

Problema que resuelve
---------------------
En Odoo, los impuestos de las lineas de un pedido de venta se calculan cuando
se carga el producto. Si despues cambia la posicion fiscal del pedido (por
ejemplo, al cambiar el Tipo de Pedido de uno "no fiscal" a uno que factura por
ARCA/AFIP), las lineas ya cargadas conservan los impuestos viejos: hay que
acordarse de apretar "Actualizar impuestos".

Con posiciones fiscales que reemplazan el IVA del producto por "IVA 0%" el
efecto es grave: el pedido nace no fiscal con sus lineas en IVA 0%, se le cambia
el tipo a fiscal, y la factura electronica sale autorizada por ARCA con IVA 0%.

Que hace
--------
1. **Pedido de venta**: cuando cambia la posicion fiscal del pedido, los
   impuestos de todas las lineas se recalculan solos segun la nueva posicion.
   Es el mismo calculo que hace el boton nativo "Actualizar impuestos"; los
   precios unitarios no se tocan.

2. **Factura de cliente (Argentina)**: en los diarios de ventas que usan
   documentos fiscales no se puede validar una factura o nota de debito que
   tenga lineas con IVA 0% (codigo ARCA 3). El control corre antes de pedir el
   CAE, asi que no se consume numeracion. Las notas de credito no se controlan,
   para poder anular comprobantes ya emitidos con IVA 0%.

   Si un diario necesita emitir con IVA 0%, se habilita con el tilde
   "Permitir IVA 0%" en el diario.

Tecnico
-------
* ``sale.order.line._compute_tax_ids``: se agrega la dependencia
  ``order_id.fiscal_position_id`` y se llama a ``super()``. Sin logica propia.
* ``account.move._post``: control previo, solo ``out_invoice`` de companias
  argentinas en diarios con ``l10n_latam_use_documents``.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'l10n_ar',
    ],
    'data': [
        'views/account_journal_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
