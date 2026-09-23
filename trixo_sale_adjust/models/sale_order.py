# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import UserError

# Campos de linea que definen QUE se vendio y A CUANTO. En un pedido
# confirmado no se cambian desde el formulario: todo cambio pasa por el
# wizard "Ajustar pedido" (19.0.1.5.0, decision de Tito 22-09-2026).
_TRIXO_LOCKED_LINE_FIELDS = frozenset({
    'product_id', 'product_template_id', 'product_uom_id', 'product_uom_qty',
    'price_unit', 'discount', 'tax_ids', 'tax_id',
})


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
        # siempre sobre un pedido confirmado. Que no haya nada para aplicar lo
        # sigue controlando `action_apply`.
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

    # ------------------------------------------------------------------
    # 19.0.1.5.0: lineas congeladas en pedidos confirmados
    # ------------------------------------------------------------------
    @api.model
    def _trixo_line_commands_touch_locked(self, commands):
        """True si los comandos de `order_line` crean, borran o cambian un
        campo que define la venta (producto, embalaje, cantidad, precio,
        descuento, impuestos)."""
        for cmd in commands or []:
            if not isinstance(cmd, (list, tuple)) or not cmd:
                continue
            op = cmd[0]
            if op in (0, 2, 3, 5, 6):
                return True
            if (op == 1 and len(cmd) > 2 and isinstance(cmd[2], dict)
                    and set(cmd[2]) & _TRIXO_LOCKED_LINE_FIELDS):
                return True
        return False

    def _trixo_lines_locked(self):
        """Pedidos cuyas lineas no se pueden tocar desde el formulario. Los
        procesos del sistema (superusuario) y el propio wizard (contexto
        `trixo_adjust_allow_line_edit`) no se bloquean."""
        if self.env.su or self.env.context.get('trixo_adjust_allow_line_edit'):
            return self.browse()
        return self.filtered(lambda o: o.state == 'sale')

    def write(self, vals):
        if 'order_line' in vals and self._trixo_line_commands_touch_locked(vals['order_line']):
            locked = self._trixo_lines_locked()
            if locked:
                raise UserError(_(
                    'El pedido %s esta confirmado: sus lineas no se modifican. '
                    'Para devolver, cambiar de embalaje o agregar productos usa el '
                    'boton "Ajustar pedido".', ', '.join(locked.mapped('name')),
                ))
        return super().write(vals)

    def action_update_prices(self):
        locked = self._trixo_lines_locked()
        if locked:
            raise UserError(_(
                'El pedido %s esta confirmado: los precios de sus lineas no se '
                'actualizan. Lo que se agregue con "Ajustar pedido" sale siempre '
                'al precio vigente.', ', '.join(locked.mapped('name')),
            ))
        return super().action_update_prices()

    # ------------------------------------------------------------------
    # Facturacion desde el wizard
    # ------------------------------------------------------------------
    def _get_invoiceable_lines(self, final=False):
        """Cuando el wizard de ajuste factura, solo deben entrar las lineas
        que el ajuste agrego o re-taso. Sin esto, `_create_invoices`
        arrastraria cualquier otra linea "a facturar" de la orden dentro de
        la misma factura."""
        lines = super()._get_invoiceable_lines(final=final)
        only_ids = self.env.context.get('trixo_adjust_only_line_ids')
        if only_ids:
            lines = lines.filtered(lambda l: l.id in only_ids)
        return lines

    def _prepare_invoice(self):
        """El wizard factura lo que el cliente se lleva con el diario de la
        factura de origen (decision de Tito 22-09-2026): si devuelve algo de
        una factura fiscal, lo que se lleva sale en ese mismo diario fiscal.
        Va despues de `sale_order_type`, que tambien fija el diario."""
        vals = super()._prepare_invoice()
        journal_id = self.env.context.get('trixo_adjust_journal_id')
        if journal_id:
            vals['journal_id'] = journal_id
            # El tipo de comprobante depende del diario: que lo recalcule la
            # factura con el diario correcto.
            vals.pop('l10n_latam_document_type_id', None)
        return vals
