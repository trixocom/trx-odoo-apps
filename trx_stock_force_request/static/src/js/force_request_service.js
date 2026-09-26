/** @odoo-module **/
// Trixocom - Solicitud de forzado de stock
// Pop-up para el aprobador: al llegar una solicitud por el bus (usuario
// conectado) y al cargar el cliente web (solicitudes que quedaron pendientes).

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export const trxForceRequestService = {
    dependencies: ["bus_service", "action", "orm", "notification"],

    start(env, { bus_service, action, orm, notification }) {
        const openRequest = (id) =>
            action.doAction({
                type: "ir.actions.act_window",
                name: _t("Solicitud de forzado de stock"),
                res_model: "stock.force.request",
                res_id: id,
                views: [[false, "form"]],
                target: "new",
            });

        const openPendingList = () =>
            action.doAction("trx_stock_force_request.action_stock_force_request", {
                additionalContext: { search_default_mine: 1, search_default_pending: 0 },
            });

        bus_service.subscribe("trx_force_request", (payload) => {
            if (!payload || !payload.id) {
                return;
            }
            notification.add(
                _t("%s pide forzar stock en %s (%s). Motivo: %s",
                    payload.requester, payload.picking, payload.origin || "-", payload.reason),
                {
                    title: _t("Solicitud de forzado de stock %s", payload.name),
                    type: "warning",
                    sticky: true,
                    buttons: [
                        { name: _t("Ver y decidir"), primary: true, onClick: () => openRequest(payload.id) },
                    ],
                }
            );
            openRequest(payload.id);
        });
        bus_service.start();

        // Lo que quedo pendiente mientras el aprobador no estaba conectado.
        orm.silent
            .call("stock.force.request", "get_pending_for_me", [])
            .then((pending) => {
                if (!pending || !pending.length) {
                    return;
                }
                if (pending.length === 1) {
                    openRequest(pending[0].id);
                } else {
                    notification.add(
                        _t("Tenes %s solicitudes de forzado de stock esperando tu respuesta.", pending.length),
                        {
                            title: _t("Forzado de stock"),
                            type: "warning",
                            sticky: true,
                            buttons: [{ name: _t("Ver solicitudes"), primary: true, onClick: openPendingList }],
                        }
                    );
                }
            })
            .catch(() => {
                /* sin permisos o sin modulo cargado: no molestar */
            });
    },
};

registry.category("services").add("trx_force_request", trxForceRequestService);
