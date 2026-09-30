# Part of trx_pos_stock_sync. Author: Trixocom. License: LGPL-3.
"""Empuja los cambios de stock a las sesiones POS abiertas.

Todo movimiento de stock termina en stock.quant: _update_available_quantity
escribe 'quantity' sobre el quant existente o crea uno nuevo. Ahi se registra el
product.template afectado en el acumulador precommit de trx_pos_price_sync, que
al cerrar la transaccion notifica a cada sesion POS abierta con el template
re-leido por _load_pos_data_read. trx_pos_price_display calcula en ese read el
campo trx_pos_qty en el contexto del deposito del PdV, que es lo que muestra la
tarjeta del producto.

Una sola notificacion por transaccion aunque se muevan muchos quants, y nada se
notifica si la transaccion termina en rollback.
"""

from odoo import api, models

from odoo.addons.trx_pos_price_sync.models.pos_price_sync import _register_for_sync

# Solo cuentan para el stock disponible los quants de ubicaciones internas; los
# de transito se incluyen por si el deposito del PdV los considera.
STOCK_USAGES = ("internal", "transit")

QTY_FIELDS = ["qty_available", "free_qty", "virtual_available", "incoming_qty", "outgoing_qty"]


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _trx_pos_register_stock_sync(self):
        quants = self.filtered(lambda q: q.location_id.usage in STOCK_USAGES)
        templates = quants.product_id.product_tmpl_id.filtered("available_in_pos")
        if templates:
            # Las cantidades son computadas no almacenadas: si algo las leyo antes
            # en esta transaccion (validar un picking lee qty_available) quedan
            # en cache con el valor previo y el POS recibiria el stock viejo.
            self.env["product.product"].invalidate_model(QTY_FIELDS)
            self.env["product.template"].invalidate_model(QTY_FIELDS + ["trx_pos_qty"])
            _register_for_sync(self.env, "product.template", templates.ids)

    @api.model_create_multi
    def create(self, vals_list):
        quants = super().create(vals_list)
        # Un quant creado solo con reserva no cambia el stock disponible.
        quants.filtered("quantity")._trx_pos_register_stock_sync()
        return quants

    def write(self, vals):
        res = super().write(vals)
        if "quantity" in vals:
            self._trx_pos_register_stock_sync()
        return res
