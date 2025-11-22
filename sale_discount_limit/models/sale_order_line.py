# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('discount')
    def _check_discount_limit(self):
        """Valida que el descuento no supere el máximo permitido para el usuario."""
        for line in self:
            # Obtener el usuario actual
            current_user = self.env.user
            
            # Obtener el descuento máximo permitido para el usuario
            max_discount = current_user.max_discount
            
            # Validar solo si el descuento es mayor a 0
            if line.discount > 0:
                # Verificar si el descuento supera el máximo permitido
                if line.discount > max_discount:
                    raise UserError(
                        _('No puede aplicar un descuento de %.2f%%. '
                          'Su descuento máximo permitido es de %.2f%%.') 
                        % (line.discount, max_discount)
                    )

    @api.onchange('discount')
    def _onchange_discount_limit(self):
        """Valida el descuento en tiempo real al cambiar el valor."""
        if self.discount > 0:
            current_user = self.env.user
            max_discount = current_user.max_discount
            
            if self.discount > max_discount:
                attempted_discount = self.discount
                self.discount = max_discount
                return {
                    'warning': {
                        'title': _('Descuento No Permitido'),
                        'message': _(
                            'No puede aplicar un descuento de %.2f%%. '
                            'Su descuento máximo permitido es de %.2f%%. '
                            'El valor ha sido ajustado al máximo permitido.'
                        ) % (attempted_discount, max_discount)
                    }
                }
