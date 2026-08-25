# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Escaneo de codigos de barras en la orden de venta.

    Odoo 19: product.packaging no existe. El barcode de embalaje vive en
    product.uom (producto + unidad + barcode) y el embalaje es la UoM de la
    linea. La resolucion del escaneo pasa a ser:

    1. product.uom por barcode  -> (producto, unidad de embalaje), suma 1
       en esa unidad (1 bulto/pack).
    2. product.product por barcode o referencia interna -> producto; si
       tiene embalaje por defecto (helper de sale_default_packaging) la
       linea queda en esa unidad y suma 1 (1 bulto = N unidades), igual
       que el comportamiento del 18. Sin embalaje, suma 1 unidad.
    """
    _inherit = 'sale.order'

    barcode_scan = fields.Char(
        string='Escanear Código de Barras',
        help='Escanea el código de barras del producto para agregarlo a la orden'
    )

    def _trixo_resolve_barcode(self, barcode):
        """Devuelve (product, uom, step). uom/step ya en la unidad correcta."""
        ProductUom = self.env['product.uom']
        Product = self.env['product.product']

        # 1. Barcode de embalaje (product.uom en 19)
        pu = ProductUom.search([('barcode', '=', barcode)], limit=1)
        if pu:
            return pu.product_id, pu.uom_id, 1.0

        # 2. Barcode de producto (o referencia interna como fallback)
        product = Product.search([('barcode', '=', barcode)], limit=1)
        if not product:
            product = Product.search([('default_code', '=', barcode)], limit=1)
        if not product:
            return Product, self.env['uom.uom'], 0.0

        # Integracion con sale_default_packaging: 1 escaneo = 1 bulto
        uom = product._trixo_default_packaging_uom()
        if not uom:
            uom = product.uom_id
        return product, uom, 1.0

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        if not self.barcode_scan:
            return
        barcode = self.barcode_scan.strip()
        self.barcode_scan = False
        if not barcode:
            return

        product, uom, step = self._trixo_resolve_barcode(barcode)
        _logger.info('BARCODE_SCAN: %r -> product=%s uom=%s step=%s',
                     barcode, product.display_name if product else None,
                     uom.name if uom else None, step)

        if not product:
            return {
                'warning': {
                    'title': 'Producto no encontrado',
                    'message': f'No se encontró ningún producto ni embalaje con el código: {barcode}',
                }
            }

        if not product.sale_ok:
            return {
                'warning': {
                    'title': 'Producto no disponible para venta',
                    'message': f'El producto "{product.name}" no está disponible para venta.',
                }
            }

        # Linea existente con el mismo producto y la misma unidad
        existing = self.order_line.filtered(
            lambda l: l.product_id == product and l.product_uom_id == uom
        )
        if existing:
            line = existing[0]
            line.product_uom_qty += step
            _logger.info('BARCODE_SCAN existing_line: qty -> %s %s',
                         line.product_uom_qty, uom.name)
        else:
            self.order_line = [(0, 0, {
                'product_id': product.id,
                'name': product.display_name,
                'product_uom_id': uom.id,
                'product_uom_qty': step,
            })]
            _logger.info('BARCODE_SCAN new_line: %s x %s %s',
                         product.display_name, step, uom.name)

        # Forzar recalculo de precios con la pricelist actual (mismo criterio
        # que 18: replica el boton "Actualizar Precios"; asi el recargo de
        # sale_packaging_pricing y la pricelist aplican en vivo).
        if self.pricelist_id:
            try:
                self._recompute_prices()
            except Exception as e:
                _logger.warning('BARCODE_SCAN _recompute_prices fallo: %s', e)
