import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    getProductName(product) {
        try {
            const code = product.default_code;
            if (code) {
                return "[" + code + "] " + product.name;
            }
        } catch (e) {
            // fallback seguro
        }
        return product.name;
    },
});
