# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends(
        "product_id",
        "company_id",
        "order_id.type_id",
        "order_id.type_id.no_fiscal",
        "order_id.type_id.no_fiscal_tax_ids",
    )
    def _compute_tax_ids(self):
        """Cuando el tipo de pedido es 'No fiscal', forzar en cada linea los
        impuestos configurados en el tipo (IVA 0% / Exento o vacio). En caso
        contrario, se mantiene el calculo estandar de Odoo (super)."""
        res = super()._compute_tax_ids()
        for line in self:
            order_type = line.order_id.type_id
            if order_type and order_type.no_fiscal and not line.display_type:
                line.tax_ids = order_type.no_fiscal_tax_ids
        return res

    @api.depends(
        "product_id",
        "product_uom_id",
        "product_uom_qty",
        "order_id.pricelist_id",
    )
    def _compute_price_unit(self):
        """Recalcular el precio automaticamente cuando cambia la lista de
        precios de la orden (p.ej. al cambiar el tipo de pedido), sin tener
        que pulsar 'Actualizar precios'."""
        return super()._compute_price_unit()

    @api.depends(
        "product_id",
        "product_uom_id",
        "product_uom_qty",
        "order_id.pricelist_id",
    )
    def _compute_discount(self):
        """Idem precio: recalcular el descuento al cambiar la lista de
        precios de la orden."""
        return super()._compute_discount()
