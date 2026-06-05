/** @odoo-module **/
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { patch } from "@web/core/utils/patch";

/*
 * Tarjeta de producto del POS:
 *  - trxPriceLabel: precio de venta (getter estandar product.template.displayPriceUnit,
 *    respeta iface_tax_included del POS).
 *  - trxShowStock / trxStockQty: cantidad on-hand del producto en el deposito del
 *    punto de venta (campo trx_pos_qty cargado por el backend, ya filtrado por
 *    config.picking_type_id.warehouse_id).
 * Todo protegido para no romper la grilla si algun dato no esta disponible.
 */
patch(ProductCard.prototype, {
    get trxPriceLabel() {
        try {
            if (this.props.isComboPopup) {
                return "";
            }
            const product = this.props.product;
            if (product && typeof product.displayPriceUnit === "string") {
                return product.displayPriceUnit;
            }
        } catch (e) {
            // fallback seguro
        }
        return "";
    },

    get trxShowStock() {
        try {
            const p = this.props.product;
            return (
                !this.props.isComboPopup &&
                !!p &&
                p.is_storable === true &&
                p.trx_pos_qty !== undefined &&
                p.trx_pos_qty !== null
            );
        } catch (e) {
            return false;
        }
    },

    get trxStockQty() {
        const p = this.props.product;
        const qty = p && p.trx_pos_qty != null ? p.trx_pos_qty : 0;
        // Mostrar entero cuando no hay decimales; si los hay, 2 decimales.
        return Number.isInteger(qty) ? qty : Math.round(qty * 100) / 100;
    },

    get trxStockClass() {
        // Color del badge: verde si hay stock, rojo si es 0 o negativo.
        return this.trxStockQty > 0 ? "bg-success text-white" : "bg-danger text-white";
    },
});
