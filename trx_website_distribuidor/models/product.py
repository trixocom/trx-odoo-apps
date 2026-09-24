from odoo import models

SIN_STOCK_MSG = "<p>Sin stock en este momento: se puede pedir igual.</p>"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _is_sold_out(self):
        if self.env.user._trx_es_distribuidor():
            return False
        return super()._is_sold_out()

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        res = super()._get_additionnal_combination_info(
            product_or_template, quantity, uom, date, website)
        if res.get("is_storable") and self.env.user._trx_es_distribuidor():
            res["allow_out_of_stock_order"] = True
            res["cart_qty"] = 0
            if "free_qty" in res:
                res["show_availability"] = True
                # Mostrar siempre la cantidad, no solo por debajo del umbral.
                res["available_threshold"] = 10 ** 12
                if res["free_qty"] <= 0 and not res.get("out_of_stock_message"):
                    res["out_of_stock_message"] = SIN_STOCK_MSG
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _is_sold_out(self):
        if self.env.user._trx_es_distribuidor():
            return False
        return super()._is_sold_out()

    def _get_max_quantity(self, website, sale_order, **kwargs):
        if self.env.user._trx_es_distribuidor():
            return None
        return super()._get_max_quantity(website, sale_order, **kwargs)
