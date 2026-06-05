# -*- coding: utf-8 -*-
# Trixocom - trx_pos_price_display
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Cantidad on-hand a mostrar en la tarjeta del POS. Se calcula en el
    # contexto del deposito del punto de venta (warehouse_id), por eso el
    # numero refleja el stock del warehouse configurado en ese PdV y no el
    # global. Campo no almacenado: se computa al momento de cargar el POS.
    trx_pos_qty = fields.Float(
        string="Stock POS (deposito del PdV)",
        compute="_compute_trx_pos_qty",
        digits="Product Unit of Measure",
    )

    @api.depends_context("warehouse_id", "location", "company")
    def _compute_trx_pos_qty(self):
        # qty_available ya respeta el contexto warehouse_id/location.
        for template in self:
            template.trx_pos_qty = template.qty_available

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if "trx_pos_qty" not in fields_list:
            fields_list.append("trx_pos_qty")
        return fields_list

    @api.model
    def _load_pos_data_read(self, records, config):
        # Filtrar el stock por el deposito del punto de venta: el warehouse se
        # toma del tipo de operacion del PdV (config.picking_type_id).
        warehouse = config.picking_type_id.warehouse_id
        if warehouse:
            records = records.with_context(warehouse_id=warehouse.id)
        return super()._load_pos_data_read(records, config)
