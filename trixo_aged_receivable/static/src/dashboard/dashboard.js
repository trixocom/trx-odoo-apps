/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formatCurrency } from "@web/core/currency";
import { formatFloat } from "@web/views/fields/formatters";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const VISTAS_PARTNER = [
    [false, "list"],
    [false, "graph"],
    [false, "pivot"],
    [false, "form"],
];
const VISTAS_LINE = [
    [false, "list"],
    [false, "pivot"],
    [false, "graph"],
];

export class TrixoDeudoresDashboard extends Component {
    static template = "trixo_aged_receivable.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: null, cargando: true });
        onWillStart(() => this.cargar());
    }

    async cargar() {
        this.state.cargando = true;
        this.state.data = await this.orm.call(
            "trixo.receivable.partner",
            "trixo_get_dashboard_data",
            []
        );
        this.state.cargando = false;
    }

    get d() {
        return this.state.data || {};
    }

    /** Importe completo, con separadores de miles. */
    money(valor) {
        return formatCurrency(valor || 0, this.d.currency_id);
    }

    /** Importe abreviado para los numeros grandes de las tarjetas ($410,47M). */
    moneyCorto(valor) {
        return formatCurrency(valor || 0, this.d.currency_id, {
            humanReadable: true,
            digits: [false, 2],
        });
    }

    /** Porcentaje con el separador decimal del idioma (31,8%). */
    pct(valor) {
        return formatFloat(valor || 0, { digits: [false, 1] }) + "%";
    }

    get variacionSube() {
        return (this.d.mes && this.d.mes.delta > 0) || false;
    }

    // --- navegacion ---------------------------------------------------
    abrirDeudores() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Deudores por cliente"),
            res_model: "trixo.receivable.partner",
            domain: [["saldo", ">", 0]],
            views: VISTAS_PARTNER,
        });
    }

    abrirVencido(dias) {
        const tramos = dias === 180 ? ["mas180"] : ["a180", "mas180"];
        this.action.doAction({
            type: "ir.actions.act_window",
            name: dias === 180 ? _t("Deuda de mas de 180 dias") : _t("Deuda de mas de 90 dias"),
            res_model: "trixo.receivable.line",
            domain: [
                ["tipo", "=", "deuda"],
                ["bucket", "in", tramos],
            ],
            views: VISTAS_LINE,
            context: { search_default_group_partner: 1 },
        });
    }

    abrirTramo(key) {
        const etiqueta = (this.d.tramos.find((t) => t.key === key) || {}).label || "";
        this.action.doAction({
            type: "ir.actions.act_window",
            name: etiqueta,
            res_model: "trixo.receivable.line",
            domain: [
                ["tipo", "=", "deuda"],
                ["bucket", "=", key],
            ],
            views: VISTAS_LINE,
            context: { search_default_group_partner: 1 },
        });
    }

    abrirCliente(linea) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: linea.name,
            res_model: "trixo.receivable.line",
            domain: [["partner_id", "=", linea.id]],
            views: VISTAS_LINE,
        });
    }

    abrirAFavor() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Saldos a favor"),
            res_model: "trixo.receivable.partner",
            domain: [["saldo", "<", 0]],
            views: VISTAS_PARTNER,
        });
    }
}

registry.category("actions").add("trixo_aged_receivable.dashboard", TrixoDeudoresDashboard);
