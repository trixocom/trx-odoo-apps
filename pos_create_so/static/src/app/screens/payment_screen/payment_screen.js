/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreen.prototype, {
    /**
     * Override del método setup para modificar comportamiento
     */
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.createSaleOrderMode = true; // Flag para indicar modo de creación de SO
    },

    /**
     * Oculta el botón de validar pago estándar
     */
    get shouldShowValidateButton() {
        // Si estamos en modo crear orden de venta, no mostrar el botón de validar
        if (this.createSaleOrderMode) {
            return false;
        }
        return super.shouldShowValidateButton;
    },

    /**
     * Nuevo método para crear orden de venta
     */
    async createSaleOrder() {
        const order = this.currentOrder;
        
        // Validaciones previas
        if (!order) {
            this.notification.add(_t("No hay orden activa"), {
                type: "warning",
            });
            return;
        }

        if (!order.partner) {
            this.notification.add(_t("Debe seleccionar un cliente para crear la orden de venta"), {
                type: "warning",
            });
            return;
        }

        if (order.lines.length === 0) {
            this.notification.add(_t("No hay productos en la orden"), {
                type: "warning",
            });
            return;
        }

        try {
            // Mostrar loader (si está disponible)
            const ui = this.env.services.ui;
            if (ui && ui.block) {
                ui.block();
            }

            // Preparar datos de la orden - crear el objeto manualmente
            const orderData = {
                id: order.id,
                name: order.name,
                partner_id: order.partner?.id,
                lines: order.lines.map(line => ({
                    product_id: line.product.id,
                    qty: line.qty,
                    price_unit: line.price_unit,
                    discount: line.discount,
                    tax_ids: line.tax_ids || [],
                    full_product_name: line.full_product_name,
                })),
                pricelist_id: order.pricelist?.id,
                fiscal_position_id: order.fiscal_position?.id,
            };
            
            // Llamar al backend para crear la orden de venta
            const result = await this.orm.call(
                'pos.order',
                'create_sale_order_from_ui',
                [orderData]
            );

            if (result && result.sale_order_id) {
                // Marcar la orden como pagada/procesada
                order.finalized = true;
                
                // Mostrar notificación de éxito
                this.notification.add(
                    _t("Orden de venta %s creada exitosamente", result.sale_order_name),
                    {
                        type: "success",
                    }
                );

                // Ir a la pantalla de recibo o crear nueva orden
                this.pos.removeOrder(order);
                this.pos.addNewOrder();
                this.pos.showScreen('ProductScreen');
                
            } else if (result && result.error) {
                throw new Error(result.error);
            } else {
                throw new Error(_t("Error al crear la orden de venta"));
            }

        } catch (error) {
            console.error("Error creando orden de venta:", error);
            this.notification.add(
                _t("Error al crear la orden de venta: %s", error.message || error),
                {
                    type: "danger",
                }
            );
        } finally {
            const ui = this.env.services.ui;
            if (ui && ui.unblock) {
                ui.unblock();
            }
        }
    },

    /**
     * Override para deshabilitar el proceso de pago normal
     */
    async validateOrder(isForceValidate) {
        // Si estamos en modo crear orden de venta, redirigir a createSaleOrder
        if (this.createSaleOrderMode) {
            return this.createSaleOrder();
        }
        
        // Si no, usar el comportamiento estándar
        return super.validateOrder(isForceValidate);
    },
});

// Patch para el modelo Order para agregar propiedades adicionales
patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        this.create_sale_order = true; // Flag para indicar que debe crear SO
    },
    
    export_as_JSON() {
        const json = super.export_as_JSON();
        // Agregar campos adicionales si son necesarios para la SO
        json.create_sale_order = true;
        return json;
    },
});
