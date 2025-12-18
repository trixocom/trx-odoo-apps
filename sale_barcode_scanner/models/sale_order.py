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
        Soporta:
        1. Código de barras de Producto
        2. Código de barras de Embalaje (Packaging)
        
        Si encuentra un producto, intenta aplicar el embalaje por defecto
        si el módulo sale_default_packaging está disponible.
        """
        if not self.barcode_scan:
            return

        barcode = self.barcode_scan.strip()
        
        if not barcode:
            self.barcode_scan = False
            return

        product = False
        packaging = False
        qty_to_add = 1.0
        packaging_qty = 0.0

        # 1. Buscar primero en Embalajes (Product Packaging)
        packaging = self.env['product.packaging'].search([
            ('barcode', '=', barcode)
        ], limit=1)

        if packaging:
            product = packaging.product_id
            # Si escaneamos un packaging, asumimos que queremos 1 unidad de ese packaging
            packaging_qty = 1.0
            if packaging.qty:
                qty_to_add = packaging.qty
        else:
            # 2. Buscar en Productos
            product = self.env['product.product'].search([
                ('barcode', '=', barcode)
            ], limit=1)

            if not product:
                # Fallback: buscar por Referencia Interna
                product = self.env['product.product'].search([
                    ('default_code', '=', barcode)
                ], limit=1)
            
            # Si encontramos producto, verificar si tiene packaging por defecto
            # (Integración con sale_default_packaging)
            if product:
                if hasattr(self.env['sale.order.line'], '_get_default_packaging_for_product'):
                    try:
                        def_pack = self.env['sale.order.line']._get_default_packaging_for_product(product.id)
                        if def_pack:
                            packaging = def_pack
                            packaging_qty = 1.0
                            if packaging.qty:
                                qty_to_add = packaging.qty
                    except Exception as e:
                        _logger.warning(f'Error buscando packaging por defecto: {e}')

        if not product:
            # No se encontró el producto ni packaging
            _logger.warning(f'Producto no encontrado con código de barras: {barcode}')
            return {
                'warning': {
                    'title': 'Producto no encontrado',
                    'message': f'No se encontró ningún producto ni embalaje con el código: {barcode}'
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
        # Si estamos usando packaging, buscamos una línea con el mismo packaging
        domain = [('product_id', '=', product.id)]
        if packaging:
             domain.append(('product_packaging_id', '=', packaging.id))
        
        existing_line = self.order_line.filtered_domain(domain)

        if existing_line:
            # Si existe, incrementar la cantidad
            # Si tiene packaging, incrementamos en unidades del packaging (ej: 1 caja más)
            
            # Nota: Si sale_default_packaging está instalado, tiene lógica para sync cantidades.
            # Aquí incrementamos la cantidad total del producto (uom_qty)
            
            existing_line[0].product_uom_qty += qty_to_add
            
            # Si tenemos el campo de cantidad de packaging (del otro módulo), intentamos actualizarlo
            if packaging and hasattr(existing_line[0], 'product_packaging_qty'):
                 # Asumiendo que added qty corresponde a 1 (o más) packagings
                 existing_line[0].product_packaging_qty += packaging_qty

            _logger.info(
                f'Incrementada cantidad de {product.name} '
                f'en orden {self.name}. Nueva cantidad: {existing_line[0].product_uom_qty}'
            )
        else:
            # Si no existe, crear una nueva línea
            vals = {
                'product_id': product.id,
                'name': product.display_name,
                'product_uom_qty': qty_to_add,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
            }
            
            if packaging:
                vals['product_packaging_id'] = packaging.id
                # Soporte para campo de cantidad de packaging si existe
                vals['product_packaging_qty'] = packaging_qty

            self.order_line = [(0, 0, vals)]
            
            _logger.info(
                f'Agregado producto {product.name} a orden {self.name} '
                f'(Packaging: {packaging.name if packaging else "Ninguno"})'
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
