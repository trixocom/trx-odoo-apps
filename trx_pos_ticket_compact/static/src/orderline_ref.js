import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

// Antepone el codigo interno (default_code) al nombre del producto en la linea
// del pedido. Como la pantalla de pedido y el ticket usan el mismo componente
// Orderline (modo "display" / "receipt") y ambos leen vals.name, esto cubre los
// dos casos a la vez.
patch(Orderline.prototype, {
    get lineScreenValues() {
        const vals = super.lineScreenValues;
        try {
            const code = this.line?.product_id?.default_code;
            if (code && vals && vals.name && !vals.name.startsWith("[" + code + "]")) {
                vals.name = "[" + code + "] " + vals.name;
            }
        } catch (e) {
            // fallback seguro: nunca romper el render del POS
        }
        return vals;
    },
});
