# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
    Extensión del modelo de orden de venta para agregar funcionalidad
    de escaneo de códigos de barras.
    """
    _inherit = 'sale.order'

    # Campo para escanear códigos de barras
    barcode_scan = fields.Char(
        string='Escanear Código de Barras',
        help='Escanea el código de barras del producto para agregarlo a la orden'
    )

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """
        Procesa el código de barras escaneado y agrega el producto a las líneas.
        
        Flujo:
        1. Busca el producto por código de barras
        2. Si existe, verifica si ya está en las líneas
        3. Si ya existe, incrementa la cantidad en 1
        4. Si no existe, crea una nueva línea con cantidad 1
        5. Limpia el campo de escaneo
        """
        if not self.barcode_scan:
            return

        barcode = self.barcode_scan.strip()
        
        if not barcode:
            self.barcode_scan = False
            return

        # Buscar el producto por código de barras
        product = self.env['product.product'].search([
            ('barcode', '=', barcode)
        ], limit=1)

        if not product:
            # No se encontró el producto
            _logger.warning(f'Producto no encontrado con código de barras: {barcode}')
            return {
                'warning': {
                    'title': 'Producto no encontrado',
                    'message': f'No se encontró ningún producto con el código de barras: {barcode}'
                }
            }

        # Verificar que el producto se pueda vender
        if not product.sale_ok:
            _logger.warning(f'Producto {product.name} no se puede vender')
            self.barcode_scan = False
            return {
                'warning': {
                    'title': 'Producto no disponible para venta',
                    'message': f'El producto "{product.name}" no está disponible para venta.'
                }
            }

        # Buscar si el producto ya existe en las líneas de orden
        existing_line = self.order_line.filtered(
            lambda line: line.product_id.id == product.id
        )

        if existing_line:
            # Si existe, incrementar la cantidad
            existing_line[0].product_uom_qty += 1
            _logger.info(
                f'Incrementada cantidad de {product.name} '
                f'en orden {self.name}. Nueva cantidad: {existing_line[0].product_uom_qty}'
            )
        else:
            # Si no existe, crear una nueva línea
            self.order_line = [(0, 0, {
                'product_id': product.id,
                'name': product.display_name,
                'product_uom_qty': 1,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
            })]
            _logger.info(
                f'Agregado producto {product.name} a orden {self.name}'
            )

        # Limpiar el campo de escaneo
        self.barcode_scan = False


class SaleOrderLine(models.Model):
    """
    Extensión del modelo de línea de orden de venta.
    Podría usarse para agregar funcionalidad adicional en el futuro.
    """
    _inherit = 'sale.order.line'

    # Aquí puedes agregar campos adicionales si los necesitas
    # Por ejemplo, un campo para tracking de escaneos:
    # 
    # scanned = fields.Boolean(
    #     string='Escaneado',
    #     default=False,
    #     help='Indica si este producto fue agregado mediante escaneo'
    # )


# =============================================================================
# NOTAS DE DESARROLLO:
# =============================================================================
#
# FUNCIONAMIENTO CON LECTOR USB:
# -------------------------------
# Los lectores de código de barras USB funcionan como un teclado.
# Cuando escaneas un código:
# 1. El lector "tipea" el código en el campo activo
# 2. Normalmente envía un ENTER al final
# 3. Esto dispara el onchange automáticamente
#
# MEJORAS FUTURAS POSIBLES:
# -------------------------
# 1. Agregar campo de cantidad a escanear
# 2. Permitir escaneo de varios productos consecutivos
# 3. Agregar sonido de confirmación
# 4. Mostrar notificación visual al agregar producto
# 5. Permitir configurar comportamiento (incrementar vs nueva línea)
# 6. Agregar log de escaneos
# 7. Soporte para códigos QR
# 8. Validación de stock disponible antes de agregar
#
# COMPATIBILIDAD:
# ---------------
# * Odoo 18 EE/CE
# * Requiere módulo 'sale' instalado
# * Compatible con cualquier lector USB
# * No requiere módulo 'barcodes' de Odoo
#
# =============================================================================
