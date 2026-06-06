/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

/**
 * ElectroQL / Trixocom: "Facturar" por defecto OFF.
 *
 * l10n_ar_pos (localizacion AR estandar) fuerza order.to_invoice = true para
 * companias argentinas al entrar a la pantalla de cobro (onMounted). En el
 * retail de ElectroQL no se factura siempre: lo decide el cajero con el toggle
 * de la primera pantalla. Revertimos ese auto-set, preservando lo que el cajero
 * ya haya elegido, y respetando el caso reembolso de una factura (que el POS
 * base obliga a facturar y no se debe destildar).
 *
 * Debe cargar DESPUES de l10n_ar_pos -> el modulo declara l10n_ar_pos en depends.
 */
patch(PaymentScreen.prototype, {
    onMounted() {
        const order = this.currentOrder;
        const before = order ? order.isToInvoice() : false;
        super.onMounted();
        if (!order) {
            return;
        }
        const lockedByRefund = Boolean(
            order.isRefund &&
            order.lines?.[0]?.refunded_orderline_id?.order_id?.isToInvoice()
        );
        if (!lockedByRefund) {
            order.setToInvoice(before);
        }
    },
});
