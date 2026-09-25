from odoo import api, fields, models

from .product import check_field_access_negado

GRUPOS_COSTO = "base.group_user,!trx_sale_restricted_salesman.group_restricted_salesman"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # margen del pedido (sale_margin): nunca visible para el vendedor restringido
    margin = fields.Monetary(groups=GRUPOS_COSTO)
    margin_percent = fields.Float(groups=GRUPOS_COSTO)

    def _check_field_access(self, field, operation):
        return check_field_access_negado(self, super()._check_field_access, field, operation)

    trx_vendedor_restringido = fields.Boolean(compute="_compute_trx_vendedor_restringido")

    def _compute_margin(self):
        # margen (sale_margin): el vendedor restringido no lo puede leer; se calcula como sistema
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(SaleOrder, self.sudo())._compute_margin()
        return super()._compute_margin()

    @api.depends_context("uid")
    def _compute_trx_vendedor_restringido(self):
        valor = self.env.user._trx_es_vendedor_restringido()
        for order in self:
            order.trx_vendedor_restringido = valor

    def _compute_pricelist_id(self):
        super()._compute_pricelist_id()
        lista = self.env.user._trx_lista_vendedor()
        if lista:
            for order in self.filtered(lambda o: o.state in ("draft", "sent")):
                order.pricelist_id = lista

    @api.model_create_multi
    def create(self, vals_list):
        lista = self.env.user._trx_lista_vendedor()
        if lista:
            for vals in vals_list:
                vals["pricelist_id"] = lista.id
        return super().create(vals_list)

    def write(self, vals):
        lista = self.env.user._trx_lista_vendedor()
        if lista and "pricelist_id" in vals:
            vals = dict(vals, pricelist_id=lista.id)
        return super().write(vals)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_price = fields.Float(groups=GRUPOS_COSTO)
    margin = fields.Float(groups=GRUPOS_COSTO)
    margin_percent = fields.Float(groups=GRUPOS_COSTO)

    def _check_field_access(self, field, operation):
        return check_field_access_negado(self, super()._check_field_access, field, operation)

    def _compute_margin(self):
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(SaleOrderLine, self.sudo())._compute_margin()
        return super()._compute_margin()

    def _compute_purchase_price(self):
        # sale_margin lee el costo del producto: para el vendedor restringido,
        # como sistema (él no puede leer el costo).
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(SaleOrderLine, self.sudo())._compute_purchase_price()
        return super()._compute_purchase_price()
