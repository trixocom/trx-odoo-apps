from odoo import models

P = "trx_website_distribuidor."


class ResUsers(models.Model):
    _inherit = "res.users"

    def _trx_es_distribuidor(self):
        user = self or self.env.user
        return bool(user) and user[:1].has_group(P + "group_distribuidor")

    def _trx_ve_no_publicados(self):
        if not self._trx_es_distribuidor():
            return False
        rule = self.env.ref(P + "rule_distribuidor_product_template", raise_if_not_found=False)
        return bool(rule and rule.sudo().active)

    def _trx_ids_param(self, key):
        raw = self.env["ir.config_parameter"].sudo().get_param(P + key) or ""
        return [int(x) for x in raw.replace(" ", "").split(",") if x.isdigit()]

    def _trx_dominio_excluidos(self):
        """Productos que el distribuidor NO ve (categorías internas y marcas)."""
        domain = []
        categs = self._trx_ids_param("excluir_categorias")
        if categs:
            domain.append(("categ_id", "not child_of", categs))
        marcas = self._trx_ids_param("excluir_marcas")
        if marcas and "product_brand_id" in self.env["product.template"]._fields:
            domain += ["|", ("product_brand_id", "=", False), ("product_brand_id", "not in", marcas)]
        return domain
