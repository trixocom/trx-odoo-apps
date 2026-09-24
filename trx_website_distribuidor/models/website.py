from odoo import models
from odoo.fields import Domain


class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        if not self.env.user._trx_ve_no_publicados():
            return super().sale_product_domain()
        # Igual que para un usuario interno, pero manteniendo el filtro de
        # servicios que no se venden por la web.
        return Domain.AND([
            self._product_domain(),
            self.get_current_website().website_domain(),
            [("service_tracking", "in",
              self.env["product.template"]._get_saleable_tracking_types())],
        ])
