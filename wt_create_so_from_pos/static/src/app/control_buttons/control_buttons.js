import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

patch(ControlButtons.prototype, {
    setup(){
        super.setup()
        this.dialogService = useService("dialog");
    },
    async clickCreateSaleOrder(){
        var self = this
        const order = this.pos.getOrder();
        const partner = order.getPartner();
        if(!partner){
            this.dialogService.add(AlertDialog, {
                body: "Seleccione un Cliente.",
                title: "Falta el Cliente",
                confirm: () => {},
                confirmLabel: "Cerrar",
            });
            return;
        }
        if(!order.getOrderlines().length){
            this.dialogService.add(AlertDialog, {
                body: "No hay productos para la Orden de Venta.",
                title: "Faltan Productos",
                confirm: () => {},
                confirmLabel: "Cerrar",
            });
            return;
        }
        const oderdetails = {};
        for (const line of order.getOrderlines()) {
            oderdetails[line.id] = { 
                product: line.product_id.id, 
                quantity: line.qty,
                price: line.price_unit,
                discount: line.discount,
            };
        }
        oderdetails['partner_id'] = order.getPartner().id
        if(0 > 0){
            oderdetails['tax_amount'] = 0
        }
        const result = await this.pos.data.call("sale.order", "craete_saleorder_from_pos", [oderdetails]);
        if(result){
            this.dialogService.add(ConfirmationDialog, {
                title: '¡Exitoso!',
                body: `¡Orden de Venta ${result.name} creada exitosamente!`,
                confirmLabel: "Confirmar Orden",
                cancelLabel: "Aceptar",
                confirm: () => {
                    this.pos.data.call('sale.order', 'action_confirm', [result.id]);
                },
                cancel: async () => {},
                dismiss: async () => {},
            });
            order.partner_id = false;
        }
        const lines = [];
        for (const line of order.getOrderlines()) {
            lines.push(line)
        }
        for (var l = 0; l < lines.length; l++) {
            lines[l].delete()
        }
    }
});
