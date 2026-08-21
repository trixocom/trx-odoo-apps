/** @odoo-module **/
// Copyright 2026 Trixocom — License OPL-1.
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, onWillDestroy } from "@odoo/owl";

export class TrxCobranzaDashboard extends Component {
    static template = "trx_cobranza_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, cargando: true, ultima: "" });
        onWillStart(() => this.cargar());
        onMounted(() => {
            this._timer = setInterval(() => this.cargar(), 60000);
        });
        onWillDestroy(() => {
            if (this._timer) {
                clearInterval(this._timer);
            }
        });
    }

    async cargar() {
        try {
            const data = await this.orm.call("trx.cobranza.dashboard", "get_data", []);
            this.state.data = data;
            this.state.ultima = new Date().toLocaleTimeString("es-AR");
        } finally {
            this.state.cargando = false;
        }
    }

    fmt(v) {
        const m = (this.state.data && this.state.data.moneda) || "$";
        return m + " " + (v || 0).toLocaleString("es-AR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    abrir(model, id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("trx_cobranza_dashboard", TrxCobranzaDashboard);
