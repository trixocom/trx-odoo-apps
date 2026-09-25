from odoo import models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_applicable_rules(self, products, date, **kwargs):
        # El vendedor restringido no puede leer las reglas (cómo está armada la
        # lista), pero el precio se tiene que calcular igual: se buscan como sistema.
        if self.env.user._trx_es_vendedor_restringido() and not self.env.su:
            return super(ProductPricelist, self.sudo())._get_applicable_rules(products, date, **kwargs)
        return super()._get_applicable_rules(products, date, **kwargs)
