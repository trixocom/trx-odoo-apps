from odoo import api, fields, models

CAMPOS_OCULTOS = ("margin", "margin_percent", "purchase_price")


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "trx.ocultar.campos.mixin"]
    _trx_campos_ocultos = CAMPOS_OCULTOS


    trx_vendedor_restringido = fields.Boolean(compute="_compute_trx_vendedor_restringido")

    def _add_precomputed_values(self, vals_list):
        # Odoo precalcula al crear los campos "precompute" (margen incluido) con el
        # usuario actual; el vendedor restringido no los puede leer: como sistema.
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(SaleOrder, self.sudo())._add_precomputed_values(vals_list)
        return super()._add_precomputed_values(vals_list)

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
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "trx.ocultar.campos.mixin"]
    _trx_campos_ocultos = CAMPOS_OCULTOS


    def _add_precomputed_values(self, vals_list):
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(SaleOrderLine, self.sudo())._add_precomputed_values(vals_list)
        return super()._add_precomputed_values(vals_list)

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


class SaleReport(models.Model):
    _name = "sale.report"
    _inherit = ["sale.report", "trx.ocultar.campos.mixin"]
    _trx_campos_ocultos = ("margin", "purchase_price")
