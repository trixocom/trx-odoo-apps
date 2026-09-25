from odoo import api, fields, models

CAMPOS_OCULTOS = ("margin", "margin_percent", "purchase_price")


def _restringido(model):
    return not model.env.su and model.env.user._trx_es_vendedor_restringido()


def _ocultar_campos(model, res):
    if _restringido(model):
        for fname in CAMPOS_OCULTOS:
            res.pop(fname, None)
    return res


def _quitar_de_vista(model, arch):
    if _restringido(model):
        xp = " or ".join("@name='%s'" % f for f in CAMPOS_OCULTOS)
        for node in arch.xpath("//field[%s]" % xp):
            node.getparent().remove(node)
    return arch


def _anular_campos(model, rows):
    if _restringido(model):
        for row in rows:
            for fname in CAMPOS_OCULTOS:
                if fname in row:
                    row[fname] = 0.0
    return rows


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Margen del pedido (sale_margin): el vendedor restringido nunca lo ve.
    # No se bloquea por permiso de campo (cualquier pantalla que lo pida fallaría
    # entera): se oculta de las pantallas y se devuelve en 0.
    def fields_get(self, allfields=None, attributes=None):
        return _ocultar_campos(self, super().fields_get(allfields, attributes))

    def _read_format(self, fnames, load="_classic_read"):
        return _anular_campos(self, super()._read_format(fnames, load))

    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        return _quitar_de_vista(self, arch), view

    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        # la vista cacheada se distingue para el vendedor restringido
        return super()._get_view_cache_key(view_id, view_type, **options) + (_restringido(self),)

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
    _inherit = "sale.order.line"

    def fields_get(self, allfields=None, attributes=None):
        return _ocultar_campos(self, super().fields_get(allfields, attributes))

    def _read_format(self, fnames, load="_classic_read"):
        return _anular_campos(self, super()._read_format(fnames, load))

    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        return _quitar_de_vista(self, arch), view

    def _get_view_cache_key(self, view_id=None, view_type="form", **options):
        # la vista cacheada se distingue para el vendedor restringido
        return super()._get_view_cache_key(view_id, view_type, **options) + (_restringido(self),)

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
