{
    'name': 'POS Mercado Pago (Orders API)',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Point Smart de Mercado Pago en el POS de Odoo 19 usando la Orders API (reemplaza pos_mercado_pago, que usa la Point Integration API deprecada)',
    'description': """
POS Mercado Pago (Orders API) para Odoo 19 CE
=============================================

Backport a Odoo 19 del módulo ``pos_mercado_pago`` de odoo/odoo ``master``
(commit c89bb6b, 2026-09-20), que migró de la *Point Integration API*
(``/point/integration-api/...``, deprecada por Mercado Pago) a la
*Orders API* (``/v1/orders`` + ``/terminals/v1``).

- Cobro en el POS con terminal Point Smart en modo PDV: Odoo crea la order,
  el cliente paga en el terminal, Mercado Pago avisa por webhook
  (``/pos_mercado_pago/notification``, evento "Order (Mercado Pago)") y el POS
  confirma la línea de pago; con "Validar automáticamente el pago por terminal"
  el pedido se valida solo.
- Reembolso total o parcial de una order desde el backend
  (``mp_order_refund``) y desde el POS cuando el framework lo permite.
- Compatible con el sandbox oficial de Mercado Pago (credenciales de prueba y
  terminal virtual ``SBX0000001``).

No instalar junto con ``pos_mercado_pago`` (mismo selector de terminal
``mercado_pago`` y mismos campos ``mp_*``): desinstalar ese antes.
""",
    'author': 'Trixocom',
    'website': 'https://trixocom.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'trx_pos_mercado_pago/static/**/*',
        ],
    },
    'pre_init_hook': 'pre_init_check',
    'installable': True,
    'application': False,
}
