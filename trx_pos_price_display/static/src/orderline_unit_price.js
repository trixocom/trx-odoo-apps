/** @odoo-module **/
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

/*
 * En Odoo 19 el precio unitario "X / unidad" de cada linea del ticket solo se
 * muestra cuando la cantidad es distinta de 1 o el precio fue editado a mano
 * (price_type != 'original'). En Odoo 16 se mostraba siempre. Este patch repone
 * ese comportamiento: en pantalla siempre muestra el unitario.
 */
patch(Orderline.prototype, {
    get lineScreenValues() {
        const vals = super.lineScreenValues;
        try {
            const line = this.line;
            if (
                this.props.mode === "display" &&
                line &&
                line.order_id &&
                !this.props.basic_receipt &&
                !line.combo_parent_id &&
                line.price !== 0 &&
                !vals.displayPriceUnit
            ) {
                const uom = line.product_id && line.product_id.uom_id
                    ? line.product_id.uom_id.name
                    : "";
                vals.displayPriceUnit = `${line.currencyDisplayPriceUnit} / ${uom}`;
            }
        } catch (e) {
            // si algo falla, devolvemos los valores originales sin romper la linea
        }
        return vals;
    },
});
