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


def _ean13_rescue(records, name, domain, operator, results, limit):
    """Antepone a ``results`` el match EXACTO por ``barcode`` completado con
    ceros a la izquierda (zfill a 13) cuando el termino es puramente numerico y
    mas corto que 13. Asi el escaneo de una etiqueta a la que le falta el/los
    cero(s) a la izquierda trae el producto correcto, aun si otro producto
    matchea por nombre/codigo y de otro modo lo taparia.

    ``records`` puede ser product.product o product.template; en ambos casos el
    campo ``barcode`` resuelve al codigo de barras de la(s) variante(s).
    """
    term = name.strip() if isinstance(name, str) else ''
    if not (operator in _POSITIVE_OPERATORS
            and term.isdigit()
            and _MIN_LENGTH <= len(term) < _EAN13_LENGTH):
        return results

    padded = term.zfill(_EAN13_LENGTH)
    full_domain = Domain(domain or Domain.TRUE) & Domain('barcode', '=', padded)
    matches = records.search_fetch(full_domain, ['display_name'], limit=limit)
    if not matches:
        return results

    existing_ids = {res[0] for res in results}
    extra = [
        (record.id, record.display_name)
        for record in matches.sudo()
        if record.id not in existing_ids
    ]
    if not extra:
        return results

    results = extra + results
    if limit:
        results = results[:limit]
    return results


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        results = super().name_search(name, domain, operator, limit)
        return _ean13_rescue(self, name, domain, operator, results, limit)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        # La linea de pedido de venta busca sobre product.template
        # (product_template_id), por eso el rescate debe estar tambien aca.
        results = super().name_search(name, domain, operator, limit)
        return _ean13_rescue(self, name, domain, operator, results, limit)
