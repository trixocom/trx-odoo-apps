from odoo import models

class ReportProductLabel4xA4(models.AbstractModel):
    _name = 'report.trixo_product_label.report_producttemplatelabel4xa4'
    _description = 'Product Label Report 4xA4'

    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
            
        quantity_by_product = data.get('quantity_by_product', {})
        active_model = data.get('active_model')
        
        if active_model == 'product.template':
            products = self.env['product.template'].browse(int(p) for p in quantity_by_product.keys())
        else:
            products = self.env['product.product'].browse(int(p) for p in quantity_by_product.keys())
        
        final_docs = []
        for product in products:
            qty = quantity_by_product.get(str(product.id), 1)
            for _ in range(qty):
                final_docs.append(product)
                
        return {
            'doc_ids': data.get('ids'),
            'doc_model': active_model,
            'docs': final_docs,
            'data': data,
        }
