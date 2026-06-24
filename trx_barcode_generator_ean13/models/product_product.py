# Copyright 2026 Trixocom
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
from odoo import _, models
from odoo.exceptions import UserError

# Prefijo GS1 de uso interno / distribución restringida (rangos 20-29).
# No corresponde a un código registrado globalmente, por lo que es seguro
# usarlo para códigos generados internamente sin colisionar con EAN reales.
EAN13_INTERNAL_PREFIX = "20"


class ProductProduct(models.Model):
    _inherit = "product.product"

    @staticmethod
    def _ean13_check_digit(code12):
        """Devuelve el dígito verificador (str) para 12 dígitos EAN13."""
        code12 = str(code12).zfill(12)
        total = sum(
            (3 if i % 2 == 0 else 1) * int(d)
            for i, d in enumerate(reversed(code12))
        )
        return str((10 - total % 10) % 10)

    def _build_ean13(self, base_number):
        """Construye un EAN13 (13 dígitos) a partir de un número base.

        El prefijo de uso interno queda al inicio y el número base se
        rellena con ceros en el espacio restante hasta completar 12 dígitos.
        """
        free_digits = 12 - len(EAN13_INTERNAL_PREFIX)
        body = EAN13_INTERNAL_PREFIX + str(base_number).zfill(free_digits)
        return body + self._ean13_check_digit(body)

    def _generate_unique_ean13(self):
        """Genera un EAN13 único basado en el id de la variante.

        Si por algún motivo el código ya está en uso (p. ej. cargado
        manualmente en otro producto), busca el siguiente disponible.
        """
        self.ensure_one()
        # El id de la variante garantiza unicidad de origen.
        offset = 0
        # Espacio disponible para el número base dentro de los 12 dígitos.
        max_base = 10 ** (12 - len(EAN13_INTERNAL_PREFIX)) - 1
        while True:
            base = self.id + offset
            if base > max_base:
                raise UserError(
                    _("No fue posible generar un EAN13 disponible.")
                )
            candidate = self._build_ean13(base)
            exists = self.with_context(active_test=False).search_count(
                [("barcode", "=", candidate)]
            )
            if not exists:
                return candidate
            offset += 1

    def action_generate_ean13(self):
        """Genera y asigna un EAN13 a las variantes que no tengan código."""
        for product in self:
            if product.barcode:
                continue
            product.barcode = product._generate_unique_ean13()
        return True
