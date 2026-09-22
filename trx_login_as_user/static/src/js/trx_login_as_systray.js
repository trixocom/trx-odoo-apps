/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";

/**
 * Icono de la barra superior para abrir la sesion de otro usuario y para
 * volver a la propia.
 *
 * Solo se dibuja si session_info dice que el usuario puede suplantar, o si la
 * sesion actual proviene de una suplantacion (asi el usuario suplantado, que
 * no tiene el permiso, igual puede volver). El permiso real se verifica en el
 * servidor: esconder el icono es cosmetica, no seguridad.
 */
export class TrxLoginAsSystray extends Component {
    static template = "trx_login_as_user.SystrayItem";
    static props = {};

    setup() {
        this.action = useService("action");
        const info = session.trx_login_as || {};
        this.canSwitch = Boolean(info.can_switch);
        this.impersonating = Boolean(info.origin_uid);
    }

    onClickSwitch() {
        this.action.doAction("trx_login_as_user.trx_login_as_user_action");
    }

    async onClickBack() {
        const result = await rpc("/trx_login_as/back", {});
        window.location = (result && result.url) || "/odoo";
    }
}

registry.category("systray").add(
    "trx_login_as_user.SystrayItem",
    { Component: TrxLoginAsSystray },
    { sequence: 1 }
);
