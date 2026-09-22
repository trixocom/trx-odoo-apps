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
        ya cargadas en "Devuelve"."""
        self.ensure_one()
        self._trixo_adjust_check_order()
        wizard = self.env['sale.order.adjust'].create({'order_id': self.id})
        wizard._populate_lines()
        wizard._apply_requested_quantities(
            self.env.context.get('trixo_adjust_new_qty'))
        # 19.0.1.3.0: el wizard es el punto de entrada del ajuste, asi que abre
        # siempre sobre un pedido confirmado. Antes exigia haber modificado las
        # lineas primero; ahora lo que hay que hacer se carga adentro (bajar
        # cantidades y, si el cliente cambia de embalaje, "Se lleva"). Que no
        # haya nada para aplicar lo sigue controlando `action_apply`.
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
