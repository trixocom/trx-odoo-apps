/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

/**
 * Compact toggle button for "invoice this order".
 * Lives in the ControlButtons row of ProductScreen (the first POS screen),
 * replacing the larger button that used to be in PaymentScreen.
 *
 * Behaviour mirrors the original PaymentScreenButtons one-to-one:
 *   - reads/writes order.to_invoice via setToInvoice/isToInvoice
 *   - greys out when pos.config.canInvoice is false
 *   - locks ON when refunding an already-invoiced order
 */
export class InvoiceToggleButton extends Component {
    static template = "trx_pos_invoice_toggle.InvoiceToggleButton";
    static props = {};

    setup() {
        this.pos = usePos();
        this.notification = useService("notification");
    }

    get currentOrder() {
        return this.pos.getOrder();
    }

    get isToInvoice() {
        return Boolean(this.currentOrder?.isToInvoice());
    }

    get canInvoice() {
        return Boolean(this.pos.config.canInvoice);
    }

    /**
     * If this order refunds a previously-invoiced order, the original POS
     * forces invoice = true and disables the button. Same here.
     */
    get isLockedByRefund() {
        const order = this.currentOrder;
        if (!order) {
            return false;
        }
        return Boolean(
            order.lines?.[0]?.refunded_orderline_id?.order_id?.isToInvoice()
        );
    }

    get title() {
        if (!this.canInvoice) {
            return _t("Facturación no disponible (configurar diario)");
        }
        return this.isToInvoice
            ? _t("Emitir Factura fiscal (activado)")
            : _t("Emitir solo Recibo (sin factura)");
    }

    onClick() {
        if (!this.canInvoice) {
            this.notification.add(
                _t(
                    "To enable invoice creation, please add a journal for it in the settings."
                ),
                { type: "warning" }
            );
            return;
        }
        if (this.isLockedByRefund) {
            return;
        }
        this.currentOrder.setToInvoice(!this.isToInvoice);
    }
}
