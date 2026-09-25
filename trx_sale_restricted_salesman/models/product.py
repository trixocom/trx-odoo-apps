from odoo import api, fields, models

from .ocultar import restringido

CAMPOS_PRECIO_PUBLICO = ("list_price", "lst_price")


class ProductoPrecioVendedorMixin(models.AbstractModel):
    """Para el vendedor restringido, el precio que ve en productos es el de SU
    lista (la fijada en su ficha), no el precio público."""
    _name = "trx.producto.precio.vendedor.mixin"
    _description = "Precio de la lista del vendedor restringido"

    trx_precio_vendedor = fields.Monetary(
        string="Su precio", compute="_compute_trx_precio_vendedor",
        currency_field="currency_id",
        help="Precio de la lista de precios fijada en la ficha del vendedor (sin impuestos).")

    @api.depends_context("uid", "company")
    def _compute_trx_precio_vendedor(self):
        lista = self.env.user._trx_lista_vendedor()
        if not lista or not self:
            for rec in self:
                rec.trx_precio_vendedor = rec.list_price if "list_price" in rec._fields else 0.0
            return
        precios = lista._get_products_price(self, 1.0)
        for rec in self:
            rec.trx_precio_vendedor = precios.get(rec.id, 0.0)

    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if restringido(self) and self.env.user._trx_lista_vendedor():
            cond = " or ".join("@name='%s'" % n for n in CAMPOS_PRECIO_PUBLICO)
            # solo nodos de este modelo (no los de sub-vistas de otro modelo)
            for node in arch.xpath("//field[%s]" % cond):
                if any(a.tag == "field" for a in node.iterancestors()):
                    continue
                node.set("name", "trx_precio_vendedor")
                node.set("readonly", "1")
                node.set("string", "Su precio")
                for attr in ("on_change", "optional", "invisible", "column_invisible"):
                    node.attrib.pop(attr, None)
                if view_type == "list":
                    node.set("optional", "show")
            for node in arch.xpath("//label[@for='list_price' or @for='lst_price']"):
                node.set("for", "trx_precio_vendedor")
                node.set("string", "Su precio")
            for node in arch.xpath("//field[@name='tax_string']"):
                node.set("invisible", "1")
        return arch, view


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "trx.ocultar.campos.mixin", "trx.producto.precio.vendedor.mixin"]
    _trx_campos_ocultos = ("standard_price",)


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "trx.ocultar.campos.mixin", "trx.producto.precio.vendedor.mixin"]
    _trx_campos_ocultos = ("standard_price",)
