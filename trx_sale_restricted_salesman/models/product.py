from odoo import _, fields, models
from odoo.exceptions import AccessError

# El costo nunca visible para el vendedor restringido. Los cálculos de Odoo
# que lo necesitan (listas sobre costo, margen) lo leen como sistema.
GRUPOS_COSTO = "base.group_user,!trx_sale_restricted_salesman.group_restricted_salesman"


def check_field_access_negado(model, super_method, field, operation):
    """Odoo 19 niega bien el acceso con "!grupo" en field.groups, pero al armar el
    mensaje de error hace env.ref() de cada grupo y el "!" lo rompe con un
    ValueError. Se devuelve el AccessError que corresponde."""
    try:
        return super_method(field, operation)
    except ValueError:
        if field.groups and "!" in field.groups:
            raise AccessError(_("No tiene permiso para acceder al campo '%(campo)s' de %(modelo)s.",
                                campo=field.string, modelo=model._description)) from None
        raise


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(groups=GRUPOS_COSTO)

    def _check_field_access(self, field, operation):
        return check_field_access_negado(self, super()._check_field_access, field, operation)


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(groups=GRUPOS_COSTO)

    def _check_field_access(self, field, operation):
        return check_field_access_negado(self, super()._check_field_access, field, operation)
