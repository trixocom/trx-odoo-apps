from odoo import api, fields, models
from odoo.tools.float_utils import float_round

class ProductProduct(models.Model):
    _inherit = 'product.product'

    packaging_quantity_available = fields.Float(
        string='Embalajes Disponibles',
        compute='_compute_packaging_quantities',
        digits='Product Unit of Measure',
        help='Cantidad de embalajes disponibles calculada según el tipo de embalaje configurado en el sistema.'
    )
    
    packaging_virtual_available = fields.Float(
        string='Embalajes Pronosticados',
        compute='_compute_packaging_quantities',
        digits='Product Unit of Measure',
        help='Cantidad pronosticada de embalajes.'
    )

    packaging_name_display = fields.Char(
        string='Unidad de Embalaje',
        compute='_compute_packaging_quantities'
    )

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        """
        Extend context to include user's preferred warehouse if set.
        This affects qty_available, virtual_available, incoming_qty, outgoing_qty.
        Only injects if no specific warehouse/location is already requested.
        """
        if self.env.user.property_warehouse_id and not self._context.get('warehouse') and not self._context.get('warehouse_id') and not self._context.get('location'):
             # Use the correct context key 'warehouse_id' which is what _get_domain_locations looks for
             self = self.with_context(warehouse_id=self.env.user.property_warehouse_id.id)
        
        return super(ProductProduct, self)._compute_quantities_dict(lot_id, owner_id, package_id, from_date, to_date)

    @api.depends('qty_available', 'virtual_available')
    def _compute_packaging_quantities(self):
        """
        Calcula la cantidad de embalajes disponibles y pronosticados.
        """
        packaging_name_param = self.env['ir.config_parameter'].sudo().get_param('stock_packaging_report.packaging_name')
        # Si no hay parámetro, usar 'Bulto' por defecto
        packaging_name = packaging_name_param if packaging_name_param else 'Bulto'
        
        # Determine context for qty_available calculation
        context = dict(self._context)
        if self.env.user.property_warehouse_id and not context.get('warehouse') and not context.get('warehouse_id') and not context.get('location'):
             context['warehouse_id'] = self.env.user.property_warehouse_id.id
        
        for product in self.with_context(context):
            product.packaging_name_display = packaging_name
            product.packaging_quantity_available = 0.0
            product.packaging_virtual_available = 0.0
            
            # Si no hay nombre de packaging configurado, no calcular
            if not packaging_name:
                continue
            
            # Buscar el packaging con el nombre configurado para este producto
            packaging = self.env['product.packaging'].search([
                ('product_id', '=', product.id),
                ('name', '=', packaging_name)
            ], limit=1)
            
            # Si no se encuentra el packaging o no tiene qty válido, no calcular
            if not packaging or packaging.qty <= 0:
                continue
            
            # Calcular cantidades
            packaging_qty = packaging.qty
            
            product.packaging_quantity_available = float_round(
                product.qty_available / packaging_qty,
                precision_rounding=0.01
            )
            product.packaging_virtual_available = float_round(
                product.virtual_available / packaging_qty,
                precision_rounding=0.01
            )
