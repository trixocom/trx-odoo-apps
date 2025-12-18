from odoo import fields, models, api

class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[
        ('4xA4', 'Trixo - Etiqueta 1/4 A4'),
    ], ondelete={'4xA4': 'set default'})

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()

        if self.print_format == '4xA4':
            xml_id = 'trixo_product_label.report_product_label_4xa4'
            
        return xml_id, data
