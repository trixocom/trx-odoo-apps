# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.fields import Domain

# Operadores "like" positivos sobre los que aplicamos el match por palabras.
# Se excluyen los patrones explicitos ('=like' / '=ilike'), las igualdades
# y los operadores negativos, para no alterar la semantica de las busquedas
# exactas, por patron o de exclusion.
_SPLIT_OPERATORS = ('like', 'ilike')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _search_display_name(self, operator, value):
        terms = value.split() if isinstance(value, str) else []
        if operator in _SPLIT_OPERATORS and len(terms) > 1:
            _super = super()
            # Cada palabra debe matchear en alguno de los campos nativos del
            # producto (nombre, referencia interna, codigo de barras, variantes).
            # Reutilizamos el dominio nativo por termino y los combinamos con AND,
            # replicando el comportamiento del buscador del sitio web
            # (website._search_build_domain): AND de palabras, OR de campos.
            return Domain.AND([
                _super._search_display_name(operator, term) for term in terms
            ])
        return super()._search_display_name(operator, value)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        terms = name.split() if isinstance(name, str) else []
        if operator in _SPLIT_OPERATORS and len(terms) > 1:
            # El name_search del core de product.product es custom y no pasa por
            # _search_display_name para el termino completo, por eso lo adaptamos
            # aca: AND de los dominios nativos por palabra (cada uno cubre nombre,
            # referencia, codigo de barras e info de proveedor segun contexto).
            search_domain = Domain.AND([
                self._search_display_name(operator, term) for term in terms
            ])
            full_domain = Domain(domain or Domain.TRUE) & search_domain
            products = self.search_fetch(full_domain, ['display_name'], limit=limit)
            return [(product.id, product.display_name) for product in products.sudo()]
        return super().name_search(name, domain, operator, limit)
