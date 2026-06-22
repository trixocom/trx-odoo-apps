# -*- coding: utf-8 -*-
import ast
import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Campos de producto de la linea de pedido a los que se les quita el quick-create.
_PRODUCT_LINE_FIELDS = ('product_template_id', 'product_id')

# Grupo cuyos miembros SI pueden crear productos desde la linea de pedido.
_GROUP_CREATE = 'trx_sale_product_no_create.group_sale_product_create'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id=view_id, view_type=view_type, **options)
        # Solo restringimos a los usuarios que NO pertenecen al grupo habilitado.
        # Los miembros del grupo conservan las opciones "Crear" y "Crear y editar".
        if not self.env.user.has_group(_GROUP_CREATE):
            for fname in _PRODUCT_LINE_FIELDS:
                for node in arch.xpath(
                        "//field[@name='order_line']//field[@name='%s']" % fname):
                    node.set('options', self._trx_options_no_create(node.get('options')))
        return arch, view

    @staticmethod
    def _trx_options_no_create(options_attr):
        """Devuelve el string del atributo 'options' del campo agregando
        no_create=True y preservando las opciones existentes."""
        opts = {}
        if options_attr:
            try:
                opts = ast.literal_eval(options_attr)
            except (ValueError, SyntaxError):
                _logger.warning(
                    "trx_sale_product_no_create: no se pudo parsear options=%r; "
                    "se aplica solo no_create.", options_attr)
                opts = {}
        if not isinstance(opts, dict):
            opts = {}
        opts['no_create'] = True
        return repr(opts)
