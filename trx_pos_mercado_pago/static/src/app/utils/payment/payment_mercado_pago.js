// Derivado de odoo/odoo master addons/pos_mercado_pago (LGPL-3), adaptado a Odoo 19 por Trixocom.
import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";

// Tiempo antes de sugerir al operador que refresque el terminal si la order
// todavía no fue confirmada.
const REFRESH_HINT_DELAY = 30000;

export class PaymentMercadoPago extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.webhook_resolver = null;
        this.refresh_hint_timeout = null;
        this.mp_order = {};
        this.current_line = null;

        // Odoo 19: PaymentInterface no tiene connectWebSocket; se usa el data service.
        this.pos.data.connectWebSocket("MERCADO_PAGO_LATEST_MESSAGE", (payload) => {
            if (payload.config_id !== this.pos.config.id) {
                return;
            }
            if (payload.payment_method_id && payload.payment_method_id !== this.payment_method_id.id) {
                return;
            }
            const pendingLine = this.pos.getPendingPaymentLine("mercado_pago");
            if (pendingLine && pendingLine.payment_method_id.id === this.payment_method_id.id) {
                this.handleMercadoPagoWebhook(pendingLine);
            }
        });
    }

    async callPaymentMethod(method, args) {
        return await this.env.services.orm.silent.call("pos.payment.method", method, args);
    }

    _getLine(uuid) {
        const order = this.pos.getOrder();
        return (uuid && order.getPaymentlineByUuid(uuid)) || order.getSelectedPaymentline();
    }

    async createOrder(line) {
        const order = line.pos_order_id || this.pos.getOrder();
        // Los datos de "external_reference" vuelven en la notificación webhook.
        const infos = {
            type: "point",
            external_reference: `${this.pos.config.current_session_id.id}_${line.payment_method_id.id}_${order.uuid}`,
            transactions: {
                payments: [{ amount: this._formatAmount(line.amount) }],
            },
        };
        return await this.callPaymentMethod("mp_order_create", [[line.payment_method_id.id], infos]);
    }

    async getLastOrderStatus(line) {
        return await this.callPaymentMethod("mp_order_get", [
            [line.payment_method_id.id],
            this.mp_order.id,
        ]);
    }

    async sendPaymentRequest(uuid) {
        await super.sendPaymentRequest(...arguments);
        const line = this._getLine(uuid);
        this.current_line = line;
        if (line.amount < 0) {
            if (!this.pos.getOrder().isRefund) {
                this._showMsg(_t("Cannot process transactions with negative amount."), "error");
                return false;
            }
            return await this._refundOrder(line);
        }
        try {
            // Mientras se crea la order no se puede cancelar
            line.setPaymentStatus("waitingCapture");
            const mp_order = await this.createOrder(line);
            if (!("id" in mp_order)) {
                // 'errors': [{'code': '', 'message': '', 'details': [...]}]
                const errors = mp_order.errors || [];
                const msg = errors.length
                    ? errors
                          .map((e) =>
                              e.details?.length ? `${e.message}: ${e.details.join(", ")}` : e.message
                          )
                          .join("\n")
                    : mp_order.message || mp_order.errorMessage || JSON.stringify(mp_order);
                this._showMsg(msg, "error");
                return false;
            }
            // Order creada
            this.mp_order = mp_order;
            line.transaction_id = mp_order.id;
            // A partir de acá se puede cancelar (en el terminal)
            line.setPaymentStatus("waitingCard");
            this._startRefreshHint();
            // Esperar el webhook con el estado final
            return await new Promise((resolve) => {
                this.webhook_resolver = resolve;
            });
        } catch (error) {
            this._showMsg(error, _t("System error"));
            return false;
        }
    }

    async _refundOrder(line) {
        const original = this._findOriginalMpPayment(line);
        if (!original) {
            this._showMsg(
                _t("You can only refund an order that was paid for with Mercado Pago."),
                "error"
            );
            return false;
        }
        const refundAmount = Math.abs(line.amount);
        // Reembolso total: body vacío; parcial: importe + id del pago original.
        const partialAmount =
            Math.abs(refundAmount - original.amount) < 0.01 ? null : this._formatAmount(refundAmount);
        try {
            const result = await this.callPaymentMethod("mp_order_refund", [
                [line.payment_method_id.id],
                original.transactionId,
                partialAmount,
            ]);
            if (!("id" in result)) {
                this._showMsg(result.message || result.errorMessage || _t("Refund failed"), "error");
                return false;
            }
            line.transaction_id = result.id;
            return true;
        } catch (error) {
            this._showMsg(error, _t("Refund error"));
            return false;
        }
    }

    _findOriginalMpPayment(refundLine) {
        const orderToRefund = refundLine.pos_order_id?.lines?.[0]?.refunded_orderline_id?.order_id;
        const matched = orderToRefund?.payment_ids?.find(
            (l) => l.payment_method_id.use_payment_terminal === "mercado_pago" && l.transaction_id
        );
        return matched ? { transactionId: matched.transaction_id, amount: matched.amount } : null;
    }

    async sendPaymentCancel(order, uuid) {
        await super.sendPaymentCancel(...arguments);
        if (!("id" in this.mp_order)) {
            return true;
        }
        this._showMsg(_t("Mercado Pago requires cancellations directly on the terminal."), "info");
        return true;
    }

    async handleMercadoPagoWebhook(pendingLine) {
        // Sin order id: el usuario recargó la página o es un webhook viejo
        if (!("id" in this.mp_order)) {
            return;
        }
        const line = pendingLine || this.current_line || this.pos.getOrder().getSelectedPaymentline();
        let last_order_status = await this.getLastOrderStatus(line);
        // Otro id: webhook viejo, no corresponde a la order actual
        if (this.mp_order.id !== last_order_status.id) {
            return;
        }

        // El terminal necesita una acción del cliente (CVV, PIN...). Avisar y
        // seguir esperando el webhook final (processed/rejected).
        if (last_order_status.status === "action_required") {
            this._clearRefreshHint();
            this._showMsg(_t("Complete the action on the Point device to continue."), "info");
            return;
        }

        const MAX_RETRY = 5;
        const RETRY_DELAY = 1000;

        const showMessageAndResolve = (messageKey, status, resolverValue) => {
            this._clearRefreshHint();
            if (!resolverValue) {
                this._showMsg(messageKey, status);
            }
            line.setPaymentStatus("done");
            this.webhook_resolver?.(resolverValue);
            return resolverValue;
        };

        const handleFinishedOrder = (order) => {
            if (order.status === "canceled") {
                return showMessageAndResolve(_t("Payment has been canceled"), "info", false);
            }
            if (order.status === "expired") {
                return showMessageAndResolve(_t("Payment expired"), "info", false);
            }
            // El pago viene embebido en la order
            const payment = order.transactions?.payments?.[0];
            if (payment?.status === "processed") {
                if (payment.payment_method?.type) {
                    line.card_type = payment.payment_method.type;
                }
                return showMessageAndResolve(_t("Payment has been processed"), "info", true);
            }
            return showMessageAndResolve(_t("Payment has been rejected"), "info", false);
        };

        if (["processed", "canceled", "expired"].includes(last_order_status.status)) {
            return handleFinishedOrder(last_order_status);
        }
        if (["created", "at_terminal"].includes(last_order_status.status)) {
            // La order puede estar en transición (created -> at_terminal ->
            // processed) cuando llega el webhook; reintentar antes de desistir.
            return await new Promise((resolve) => {
                let retry_cnt = 0;
                const s = setInterval(async () => {
                    last_order_status = await this.getLastOrderStatus(line);
                    if (["processed", "canceled", "expired"].includes(last_order_status.status)) {
                        clearInterval(s);
                        resolve(handleFinishedOrder(last_order_status));
                    }
                    retry_cnt += 1;
                    if (retry_cnt >= MAX_RETRY) {
                        clearInterval(s);
                        resolve(
                            showMessageAndResolve(
                                _t("Payment status could not be confirmed"),
                                "error",
                                false
                            )
                        );
                    }
                }, RETRY_DELAY);
            });
        }
        return showMessageAndResolve(_t("Unknown payment status"), "error", false);
    }

    // private
    _startRefreshHint() {
        this._clearRefreshHint();
        this.refresh_hint_timeout = setTimeout(() => {
            this._showMsg(
                _t("If the payment does not appear on the Point, press the 'Refresh' button on the device."),
                "info"
            );
        }, REFRESH_HINT_DELAY);
    }

    _clearRefreshHint() {
        if (this.refresh_hint_timeout) {
            clearTimeout(this.refresh_hint_timeout);
            this.refresh_hint_timeout = null;
        }
    }

    _formatAmount(amount) {
        // Mercado Pago espera el importe como string con hasta 2 decimales;
        // respeta los decimales de la moneda (p.ej. CLP sin decimales).
        const decimals = Math.min(this.pos.currency?.decimal_places ?? 2, 2);
        return amount.toFixed(decimals);
    }

    _showMsg(msg, title) {
        this.env.services.dialog.add(AlertDialog, {
            title: _t("Mercado Pago %s", title),
            body: String(msg),
        });
    }
}

register_payment_method("mercado_pago", PaymentMercadoPago);
