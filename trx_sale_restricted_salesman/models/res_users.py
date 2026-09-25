from odoo import models

GRUPO = "trx_sale_restricted_salesman.group_restricted_salesman"


class ResUsers(models.Model):
    _inherit = "res.users"

    def _trx_es_vendedor_restringido(self):
        user = self[:1] or self.env.user
        return bool(user) and user.has_group(GRUPO)

    def _trx_lista_vendedor(self):
        """Lista de precios fijada en la ficha (partner) del vendedor restringido."""
        user = self[:1] or self.env.user
        if not user._trx_es_vendedor_restringido():
            return self.env["product.pricelist"]
        return user.sudo().partner_id.property_product_pricelist
