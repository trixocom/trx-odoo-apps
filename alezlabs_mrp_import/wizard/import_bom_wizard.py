import base64
import io
import logging
import openpyxl
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ImportBomWizard(models.TransientModel):
    _name = 'alezlabs.import.bom.wizard'
    _description = 'Import BOM from Excel'

    file = fields.Binary(string='Archivo Excel', required=True)
    filename = fields.Char(string='Nombre de Archivo')

    def import_boms(self):
        if not self.file:
            raise UserError(_("Por favor suba un archivo."))

        try:
            file_data = base64.b64decode(self.file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(_("Error al leer el archivo Excel: %s") % str(e))

        rows = list(sheet.iter_rows(values_only=True))
        
        # Data starts at Row 2 (Index 1) based on user confirmation
        # Columns Mapping:
        # 1: Parent Ref (B)
        # 3: Phase (D)
        # 4: Component Ref (E)
        # 5: Component Name (F)
        # 6: Qty (G)
        # 7: Parent Name (H)
        # 8: Version (I)
        # 9: Type (J)
        # 10: Min Qty (K)
        # 11: Method (L)
        # 12: Shrinkage (M)

        boms_data = {}
        Product = self.env['product.product']
        Template = self.env['product.template']
        Category = self.env['product.category']
        Bom = self.env['mrp.bom']
        BomLine = self.env['mrp.bom.line']
        
        # Ensure Categories exist
        cat_rm = Category.search([('name', '=', 'Materia Prima')], limit=1)
        if not cat_rm:
            cat_rm = Category.create({'name': 'Materia Prima'})
            
        cat_fg = Category.search([('name', '=', 'Producto Terminado')], limit=1)
        if not cat_fg:
            cat_fg = Category.create({'name': 'Producto Terminado'})

        for row_idx, row in enumerate(rows):
            if row_idx < 1: # Skip Header Row 0
                continue
            
            # Check row length
            if not row or len(row) < 7:
                continue

            parent_ref = str(row[1]).strip() if row[1] else False
            if not parent_ref:
                continue

            # Header Data
            header_data = {
                'ref': parent_ref,
                'name': str(row[7]).strip() if len(row) > 7 and row[7] else 'Producto Sin Nombre',
                'version': str(row[8]).strip() if len(row) > 8 and row[8] else False,
                'type': str(row[9]).strip() if len(row) > 9 and row[9] else False,
                'min_qty': str(row[10]).strip() if len(row) > 10 and row[10] else False,
                'method': str(row[11]).strip() if len(row) > 11 and row[11] else False,
                'shrinkage': row[12] if len(row) > 12 else 0.0,
            }

            if parent_ref not in boms_data:
                boms_data[parent_ref] = {
                    'header': header_data,
                    'lines': []
                }
            
            # Component Data
            comp_ref = str(row[4]).strip() if row[4] else False
            qty = row[6]
            
            if comp_ref:
                try:
                    qty = float(qty)
                except (ValueError, TypeError):
                    qty = 0.0
                
                boms_data[parent_ref]['lines'].append({
                    'ref': comp_ref,
                    'name': str(row[5]).strip() if len(row) > 5 and row[5] else 'Componente Sin Nombre',
                    'qty': qty,
                    'phase': str(row[3]).strip() if row[3] else False,
                    'sequence': row[0]
                })

        created_boms = 0
        
        for parent_ref, data in boms_data.items():
            header = data['header']
            
            # 1. Manage Parent Product
            parent_tmpl = Template.search([('default_code', '=', parent_ref)], limit=1)
            if not parent_tmpl:
                # Create Parent
                parent_tmpl = Template.create({
                    'name': header['name'],
                    'default_code': parent_ref,
                    'type': 'product', # Storable
                    'categ_id': cat_fg.id,
                    'tracking': 'lot', # Usually traceability for cosmetic products
                })
            
            # Update Parent Custom Fields
            try:
                shrinkage_val = float(header['shrinkage']) if header['shrinkage'] else 0.0
            except:
                shrinkage_val = 0.0

            parent_tmpl.write({
                'x_formula_version': header['version'],
                'x_formula_type': header['type'],
                'x_min_manufacture_qty': header['min_qty'],
                'x_elaboration_method': header['method'],
                'x_shrinkage': shrinkage_val,
            })
            
            # 2. Manage Components
            for line in data['lines']:
                comp_ref = line['ref']
                comp_product = Product.search([('default_code', '=', comp_ref)], limit=1)
                
                if not comp_product:
                    # Create Component at Template level then get variant
                    comp_tmpl = Template.create({
                        'name': line['name'],
                        'default_code': comp_ref,
                        'type': 'product',
                        'categ_id': cat_rm.id,
                    })
                    comp_product = comp_tmpl.product_variant_id

            # 3. Manage BOM
            # Find existing BOM for this product
            bom = Bom.search([('product_tmpl_id', '=', parent_tmpl.id)], limit=1)
            
            bom_vals = {
                'product_tmpl_id': parent_tmpl.id,
                'product_qty': 1.0, # Base 1
                'type': 'normal',
                'code': header['version'] or '', 
            }
            
            if bom:
                bom.write(bom_vals)
                # Remove existing lines to replace
                bom.bom_line_ids.unlink()
            else:
                bom = Bom.create(bom_vals)
                created_boms += 1
            
            # 4. Create BOM Lines
            for line in data['lines']:
                comp_product = Product.search([('default_code', '=', line['ref'])], limit=1) # Should exist now
                
                BomLine.create({
                    'bom_id': bom.id,
                    'product_id': comp_product.id,
                    'product_qty': line['qty'],
                    'x_phase': line['phase'],
                    # 'sequence': line['sequence'] # format might be string "1", "2"... 
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Completada'),
                'message': _('Se procesaron %d Fórmulas.') % len(boms_data),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
