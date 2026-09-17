# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_trixo_adjust(self):
        """Boton de cabecera "Ajustar pedido".

        Si el usuario bajo cantidades directamente en las lineas del pedido,
        el cliente web (static/src/js/adjust_button_patch.js) las saca del
        guardado y las manda en el contexto `trixo_adjust_new_qty`
        ({id de linea: nueva cantidad}); el wizard abre con esas cantidades
        ya cargadas en "Nueva cantidad"."""
        self.ensure_one()
        self._trixo_adjust_check_order()
        wizard = self.env['sale.order.adjust'].create({'order_id': self.id})
        wizard._populate_lines()
        wizard._apply_requested_quantities(
            self.env.context.get('trixo_adjust_new_qty'))
        if not wizard.has_changes:
            # Pedido sin modificar (ni bajas tomadas de las lineas ni nada
            # agregado pendiente de facturar): se explica el orden correcto.
            raise UserError(_(
                'El pedido %s no tiene cambios para ajustar.\n\n'
                'PRIMERO cambia las cantidades en las lineas del pedido (baja lo que '
                'el cliente devuelve o no lleva, subi o agrega lo que suma) y '
                'DESPUES, sin guardar, apreta el boton "Ajustar pedido": se genera la '
                'devolucion de la mercaderia, la nota de credito y, si agregaste '
                'productos, el despacho y la factura adicional.',
                self.name,
            ))
        return wizard._get_action()

    def _trixo_adjust_check_order(self):
        self.ensure_one()
        if self.state != 'sale':
            raise UserError(_(
                'Solo se pueden ajustar pedidos confirmados (estado "Orden de venta").'
            ))
        if self.locked:
            raise UserError(_(
                'El pedido %s esta bloqueado. Desbloquealo antes de ajustarlo.',
                self.name,
            ))

    def _get_invoiceable_lines(self, final=False):
        """Cuando el wizard de ajuste factura, solo deben entrar las lineas
        que el ajuste re-tasó (componentes de un combo desarmado). Sin esto,
        `_create_invoices` arrastraria cualquier otra linea "a facturar" de la
        orden dentro de la misma factura."""
        lines = super()._get_invoiceable_lines(final=final)
        only_ids = self.env.context.get('trixo_adjust_only_line_ids')
        if only_ids:
            lines = lines.filtered(lambda l: l.id in only_ids)
        return lines
