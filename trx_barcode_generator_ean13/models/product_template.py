# Copyright 2026 Trixocom
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_generate_ean13(self):
        """Genera el EAN13 en la variante única de la plantilla.

        Solo aplica a plantillas con una sola variante; en productos con
        múltiples variantes el código se genera desde cada variante.
        """
        for template in self:
            if template.barcode or template.product_variant_count != 1:
                continue
            template.product_variant_id.action_generate_ean13()
        return True
