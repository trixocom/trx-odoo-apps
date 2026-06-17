# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.fields import Domain

# Operadores positivos de autocompletado / escaneo. Sobre estos intentamos el
# rescate por relleno de ceros. Se excluyen los negativos para no alterar la
# semantica de las busquedas de exclusion.
_POSITIVE_OPERATORS = ('=', 'ilike', '=ilike', 'like', '=like')

# Longitud del codigo EAN13.
_EAN13_LENGTH = 13

# Piso de longitud para intentar el rescate. Evita disparar el relleno con
# textos numericos muy cortos (codigos internos, cantidades, etc.).
_MIN_LENGTH = 8


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        # 1) Comportamiento nativo primero. Si encuentra algo, no tocamos nada.
        results = super().name_search(name, domain, operator, limit)
        if results:
            return results

        # 2) Rescate EAN13. La etiqueta impresa a veces pierde el/los cero(s) a
        # la izquierda, por eso un EAN13 guardado como "0264709617697" no se
        # encuentra al escanear "264709617697". Si el termino es puramente
        # numerico y mas corto que 13, reintentamos un match EXACTO contra el
        # barcode completado con ceros a la izquierda (zfill a 13).
        term = name.strip() if isinstance(name, str) else ''
        if (operator in _POSITIVE_OPERATORS
                and term.isdigit()
                and _MIN_LENGTH <= len(term) < _EAN13_LENGTH):
            padded = term.zfill(_EAN13_LENGTH)
            full_domain = Domain(domain or Domain.TRUE) & Domain('barcode', '=', padded)
            products = self.search_fetch(full_domain, ['display_name'], limit=limit)
            if products:
                return [(product.id, product.display_name) for product in products.sudo()]

        return results
