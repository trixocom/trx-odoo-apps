from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _trixo_label_packaging_uom(self):
        """UoM de embalaje del producto, para las etiquetas.

        Odoo 19 elimino product.packaging: los embalajes ahora son unidades de
        medida (uom_ids). Si esta instalado sale_default_packaging se respeta su
        criterio (parametro stock_packaging_report.packaging_name); si no, se
        toma la primera UoM del producto distinta de la de referencia.
        """
        self.ensure_one()
        helper = getattr(self, '_trixo_default_packaging_uom', None)
        if helper:
            uom = helper()
            if uom:
                return uom
        return self.uom_ids.filtered(lambda u: u != self.uom_id)[:1]

    def _trixo_label_qty_per_package(self):
        """Unidades por bulto, en la UoM de referencia (1.0 si no hay embalaje)."""
        self.ensure_one()
        uom = self._trixo_label_packaging_uom()
        if not uom:
            return 1.0
        return uom._compute_quantity(1.0, self.uom_id)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _trixo_label_packaging_uom(self):
        """UoM de embalaje del producto, para las etiquetas.

        Odoo 19 elimino product.packaging: los embalajes ahora son unidades de
        medida (uom_ids). Si esta instalado sale_default_packaging se respeta su
        criterio (parametro stock_packaging_report.packaging_name); si no, se
        toma la primera UoM del producto distinta de la de referencia.
        """
        self.ensure_one()
        helper = getattr(self, '_trixo_default_packaging_uom', None)
        if helper:
            uom = helper()
            if uom:
                return uom
        return self.uom_ids.filtered(lambda u: u != self.uom_id)[:1]

    def _trixo_label_qty_per_package(self):
        """Unidades por bulto, en la UoM de referencia (1.0 si no hay embalaje)."""
        self.ensure_one()
        uom = self._trixo_label_packaging_uom()
        if not uom:
            return 1.0
        return uom._compute_quantity(1.0, self.uom_id)
