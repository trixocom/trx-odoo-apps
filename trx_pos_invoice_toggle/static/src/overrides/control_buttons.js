/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { InvoiceToggleButton } from "@trx_pos_invoice_toggle/components/invoice_toggle";

// Register the new sub-component so the inherited template can use it.
ControlButtons.components = {
    ...ControlButtons.components,
    InvoiceToggleButton,
};
