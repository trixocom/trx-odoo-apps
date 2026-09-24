from odoo import api, fields, models
from odoo.fields import Domain


class Website(models.Model):
    _inherit = "website"

    # El valor configurado sigue guardado en su columna de siempre; lo que se
    # vuelve dependiente del usuario es cómo se lee: el distribuidor ve los
    # precios SIN IVA y el resto ve exactamente lo configurado.
    show_line_subtotals_tax_selection = fields.Selection(
        compute="_compute_show_line_subtotals_tax_selection",
        inverse="_inverse_trx_tax_display",
        store=False,
    )

    @api.depends_context("uid")
    def _compute_show_line_subtotals_tax_selection(self):
        ids = [w.id for w in self if isinstance(w.id, int)]
        guardado = {}
        if ids:
            self.env.cr.execute(
                "SELECT id, show_line_subtotals_tax_selection FROM website WHERE id = ANY(%s)",
                [ids])
            guardado = dict(self.env.cr.fetchall())
        pendientes = self.filtered(lambda w: not guardado.get(w.id))
        if pendientes:
            super(Website, pendientes)._compute_show_line_subtotals_tax_selection()
        es_distribuidor = self.env.user._trx_es_distribuidor()
        for website in self:
            if es_distribuidor:
                website.show_line_subtotals_tax_selection = "tax_excluded"
            elif guardado.get(website.id):
                website.show_line_subtotals_tax_selection = guardado[website.id]

    def _inverse_trx_tax_display(self):
        for website in self:
            if isinstance(website.id, int) and website.show_line_subtotals_tax_selection:
                self.env.cr.execute(
                    "UPDATE website SET show_line_subtotals_tax_selection = %s WHERE id = %s",
                    [website.show_line_subtotals_tax_selection, website.id])

    def sale_product_domain(self):
        user = self.env.user
        if not user._trx_es_distribuidor():
            return super().sale_product_domain()
        if user._trx_ve_no_publicados():
            # Igual que para un usuario interno, pero manteniendo el filtro de
            # servicios que no se venden por la web.
            base = Domain.AND([
                self._product_domain(),
                self.get_current_website().website_domain(),
                [("service_tracking", "in",
                  self.env["product.template"]._get_saleable_tracking_types())],
            ])
        else:
            base = super().sale_product_domain()
        return Domain.AND([base, user._trx_dominio_excluidos()])
