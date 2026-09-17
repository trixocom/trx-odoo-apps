# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # ------------------------------------------------------------------
    # Boton por linea (paridad con sale_stock_ux v18)
    # ------------------------------------------------------------------
    def action_trixo_cancel_remaining(self):
        """Deja la linea en lo entregado.

        - Si no hay nada facturado por encima de lo entregado, actua en un
          click: baja `product_uom_qty` y el core cancela los movimientos
          pendientes.
        - Si hay facturado de mas, hace falta una nota de credito: abre el
          wizard prellenado con esta linea para que el usuario vea y
          confirme lo que va a pasar.
        """
        self.ensure_one()
        order = self.order_id
        order._trixo_adjust_check_order()
        if self.display_type or not self.product_id:
            return False
        if self._trixo_adjust_is_combo_parent():
            raise UserError(_(
                'La linea "%s" es la cabecera de un combo: ajusta los '
                'componentes desde "Ajustar pedido".', self.product_id.display_name,
            ))
        precision = self.env['decimal.precision'].precision_get('Product Unit')
        target = self.qty_delivered
        if float_compare(target, self.product_uom_qty, precision_digits=precision) >= 0:
            raise UserError(_('La linea "%s" no tiene cantidad pendiente de entregar.',
                              self.product_id.display_name))
        needs_wizard = float_compare(self.qty_invoiced, target, precision_digits=precision) > 0
        if 'surtido_parent_line_id' in self._fields and self.surtido_parent_line_id:
            # Componente de combo: hay que re-evaluar el combo completo.
            needs_wizard = True
        if needs_wizard:
            wizard = self.env['sale.order.adjust'].create({'order_id': order.id})
            wizard._populate_lines()
            wline = wizard.line_ids.filtered(lambda w: w.sale_line_id == self)
            wline.new_qty = target
            wizard._compute_lines_from_new_qty()
            return wizard._get_action()
        old_qty = self.product_uom_qty
        self.with_context(skip_surtido_detection=True).write({'product_uom_qty': target})
        order.message_post(body=_(
            'Cancelacion de pendiente en la linea "%(line)s": cantidad %(old)s -> %(new)s '
            '(igualada a lo entregado). Usuario: %(user)s.',
            line=self.product_id.display_name, old=old_qty, new=target,
            user=self.env.user.name,
        ))
        return True

    # ------------------------------------------------------------------
    # Helpers combo (modulo de surtidos, dependencia opcional)
    # ------------------------------------------------------------------
    def _trixo_adjust_is_combo_parent(self):
        self.ensure_one()
        return bool(
            'surtido_id' in self._fields and self.surtido_id
            and not self.surtido_parent_line_id
        )

    def _trixo_adjust_combo_children(self):
        self.ensure_one()
        if 'surtido_parent_line_id' not in self._fields:
            return self.browse()
        return self.order_id.order_line.filtered(
            lambda l: l.surtido_parent_line_id == self
        )

    # ------------------------------------------------------------------
    # Bypass controlado del chequeo "no bajar por debajo de lo entregado"
    # ------------------------------------------------------------------
    def _update_line_quantity(self, values):
        """sale_stock impide bajar `product_uom_qty` por debajo de
        `qty_delivered`. El wizard crea la devolucion ANTES de bajar la
        cantidad, pero si la devolucion queda sin validar (entrega a
        domicilio) `qty_delivered` todavia no bajo. En ese caso el wizard
        pasa este flag: la coherencia la garantiza la devolucion pendiente
        (`_get_qty_procurement` ya la descuenta, asi que no se genera
        ningun movimiento negativo extra)."""
        if self.env.context.get('trixo_adjust_skip_delivered_check'):
            # El wizard ya deja su propio mensaje en el chatter.
            return True
        if self.env.user.has_group('trixo_sale_adjust.group_sale_adjust'):
            # Misma condicion que el bloqueo del core, con un mensaje que
            # indica el camino correcto a quien puede ajustar pedidos.
            precision = self.env['decimal.precision'].precision_get('Product Unit')
            delivered = self.filtered(
                lambda l: l.product_id.type == 'consu').mapped('qty_delivered')
            if delivered and float_compare(
                    values['product_uom_qty'], max(delivered),
                    precision_digits=precision) == -1:
                raise UserError(_(
                    'No se puede guardar una cantidad menor a la ya entregada. '
                    'Baja la cantidad en la linea y, sin guardar, apreta el boton '
                    '"Ajustar pedido": genera la devolucion de la mercaderia y la '
                    'nota de credito que correspondan.'
                ))
        return super()._update_line_quantity(values)
