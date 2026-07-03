/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PhoneField, phoneField, formPhoneField } from "@web/views/fields/phone/phone_field";
import { SendWhatsAppButton } from "@trixo_whatsapp/phone_field/whatsapp_phone_button";

patch(PhoneField, {
    components: {
        ...PhoneField.components,
        SendWhatsAppButton,
    },
    defaultProps: {
        ...PhoneField.defaultProps,
        enableWa: true,
    },
    props: {
        ...PhoneField.props,
        enableWa: { type: Boolean, optional: true },
    },
});

const patchDescr = () => ({
    extractProps() {
        const props = super.extractProps(...arguments);
        const options = arguments[0].options || {};
        if (options.enable_whatsapp === false) {
            props.enableWa = false;
        }
        return props;
    },
    supportedOptions: [
        {
            label: _t("Enable WhatsApp"),
            name: "enable_whatsapp",
            type: "boolean",
            default: true,
        },
    ],
});

patch(phoneField, patchDescr());
patch(formPhoneField, patchDescr());
