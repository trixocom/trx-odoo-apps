from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _trx_es_distribuidor(self):
        user = self or self.env.user
        return bool(user) and user[:1].has_group(
            "trx_website_distribuidor.group_distribuidor")

    def _trx_ve_no_publicados(self):
        if not self._trx_es_distribuidor():
            return False
        rule = self.env.ref(
            "trx_website_distribuidor.rule_distribuidor_product_template",
            raise_if_not_found=False)
        return bool(rule and rule.sudo().active)
