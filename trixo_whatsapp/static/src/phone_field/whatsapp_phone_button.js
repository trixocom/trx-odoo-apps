/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component, status } from "@odoo/owl";

export class SendWhatsAppButton extends Component {
    static template = "trixo_whatsapp.SendWhatsAppButton";
    static props = ["*"];

    setup() {
        this.action = useService("action");
        this.title = _t("Enviar WhatsApp");
    }

    async onClick() {
        await this.props.record.save();
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                target: "new",
                name: this.title,
                res_model: "whatsapp.compose",
                views: [[false, "form"]],
                context: {
                    ...user.context,
                    default_res_model: this.props.record.resModel,
                    default_res_id: this.props.record.resId,
                    default_number_field_name: this.props.name,
                    dialog_size: "medium",
                },
            },
            {
                onClose: () => {
                    if (status(this) !== "destroyed") {
                        this.props.record.load();
                    }
                },
            }
        );
    }
}
