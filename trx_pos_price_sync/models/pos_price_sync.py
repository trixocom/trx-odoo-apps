# Part of trx_pos_price_sync. Author: Trixocom. License: LGPL-3.
"""Empuja cambios de productos y reglas de tarifa a las sesiones POS abiertas.

Mecanismo: se acumulan los ids modificados durante la transaccion (precommit,
una sola notificacion por transaccion aunque haya escrituras masivas) y antes
del commit se llama a pos.config.notify_synchronisation() -canal SYNCHRONISATION
nativo de Odoo 19- que re-lee los registros con _load_pos_data_read y los manda
por websocket. El cliente POS los upserta en su store reactivo y los persiste
en IndexedDB (listener "update" estandar de data_service), por lo que el cambio
sobrevive a un F5. Los mensajes de bus se envian junto con el commit, asi que
no se notifica nada si la transaccion termina en rollback.
"""
import logging
from collections import defaultdict

from odoo import api, models

_logger = logging.getLogger(__name__)

PRECOMMIT_KEY = "trx_pos_price_sync"

# Campos que impactan lo que el POS muestra/calcula para un producto.
TEMPLATE_SYNC_FIELDS = {
    "list_price",
    "taxes_id",
    "name",
    "default_code",
    "barcode",
    "available_in_pos",
    "pos_categ_ids",
    "pos_sequence",
    "to_weight",
}
PRODUCT_SYNC_FIELDS = {
    "list_price",
    "lst_price",
    "default_code",
    "barcode",
}
# Campos de regla de tarifa que cambian el precio calculado en el POS.
PRICELIST_ITEM_SYNC_FIELDS = {
    "fixed_price",
    "percent_price",
    "price_discount",
    "price_surcharge",
    "price_round",
    "price_min_margin",
    "price_max_margin",
    "compute_price",
    "base",
    "base_pricelist_id",
    "min_quantity",
    "date_start",
    "date_end",
    "product_tmpl_id",
    "product_id",
    "categ_id",
    "pricelist_id",
}


def _register_for_sync(env, model_name, ids):
    """Acumula ids a sincronizar y registra el flush precommit (una sola vez)."""
    if not ids:
        return
    precommit = env.cr.precommit
    if PRECOMMIT_KEY not in precommit.data:
        precommit.data[PRECOMMIT_KEY] = defaultdict(set)
        # Se registra el callback solo al crear la entrada: precommit.add
        # encola sin deduplicar y el callback debe correr una unica vez.
        precommit.add(lambda: _flush_sync(env))
    precommit.data[PRECOMMIT_KEY][model_name].update(ids)


def _flush_sync(env):
    """Notifica los registros acumulados a cada POS con sesion abierta.

    Corre en precommit: cualquier error se loguea y se traga, un fallo de
    sincronizacion nunca debe romper la escritura de un precio.
    """
    data = env.cr.precommit.data.pop(PRECOMMIT_KEY, None)
    if not data:
        return
    try:
        configs = (
            env["pos.config"]
            .sudo()
            .search([("current_session_id.state", "=", "opened")])
        )
        if not configs:
            return

        Template = env["product.template"].sudo()
        Product = env["product.product"].sudo()
        Item = env["product.pricelist.item"].sudo()

        templates = Template.browse(data.get("product.template", ())).exists()
        products = Product.browse(data.get("product.product", ())).exists()
        items = Item.browse(data.get("product.pricelist.item", ())).exists()
        # Variantes de los templates tocados: el POS trabaja sobre ambos modelos.
        products |= templates.product_variant_ids

        for config in configs:
            records = {}
            # Mismo dominio que usa el POS para cargar productos (compania,
            # available_in_pos, sale_ok, limite de categorias).
            tmpl_domain = Template._load_pos_data_domain({}, config)
            config_templates = templates.filtered_domain(tmpl_domain)
            config_products = products.filtered_domain(tmpl_domain)
            if config_templates:
                records["product.template"] = config_templates.ids
            if config_products:
                records["product.product"] = config_products.ids
            available_pricelists = config._get_available_pricelists()
            config_items = items.filtered(
                lambda i: i.pricelist_id in available_pricelists
            )
            if config_items:
                records["product.pricelist.item"] = config_items.ids
            if not records:
                continue
            config.notify_synchronisation(
                config.current_session_id.id, 0, records
            )
            _logger.debug(
                "trx_pos_price_sync: notificado config %s (sesion %s): %s",
                config.id,
                config.current_session_id.id,
                {m: len(i) for m, i in records.items()},
            )
    except Exception:  # noqa: BLE001 - no romper el commit por un fallo de sync
        _logger.exception("trx_pos_price_sync: fallo notificando cambios al POS")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        res = super().write(vals)
        if TEMPLATE_SYNC_FIELDS & vals.keys():
            _register_for_sync(self.env, "product.template", self.ids)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _register_for_sync(
            self.env,
            "product.template",
            records.filtered("available_in_pos").ids,
        )
        return records


class ProductProduct(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        res = super().write(vals)
        if PRODUCT_SYNC_FIELDS & vals.keys():
            _register_for_sync(self.env, "product.product", self.ids)
        return res


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def write(self, vals):
        res = super().write(vals)
        if PRICELIST_ITEM_SYNC_FIELDS & vals.keys():
            _register_for_sync(self.env, "product.pricelist.item", self.ids)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        _register_for_sync(self.env, "product.pricelist.item", records.ids)
        return records
