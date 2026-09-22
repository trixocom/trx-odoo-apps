/** @odoo-module **/
/*
 * Trixocom - trixo_sale_adjust
 *
 * Boton de cabecera "Ajustar pedido" sobre un pedido con lineas editadas.
 *
 * El cliente web guarda el formulario antes de ejecutar cualquier boton
 * type="object". Si el usuario bajo cantidades en las lineas por debajo de lo
 * entregado, ese guardado choca con el bloqueo del core (sale_stock
 * `_update_line_quantity`) y el boton nunca llega a ejecutarse.
 *
 * Este patch, SOLO para ese boton y SOLO en sale.order:
 *   0. cierra la edicion pendiente de la celda (`_askChanges`), porque el
 *      usuario puede apretar el boton sin salir del campo cantidad;
 *   1. toma las cantidades que el usuario bajo en las lineas ya guardadas;
 *   2. las saca del formulario (no se guardan nunca por esta via):
 *        - si era lo unico editado: descarta los cambios, no hay guardado;
 *        - si ademas hay otros cambios (cantidades aumentadas, productos
 *          agregados, etc.): restituye esas cantidades y deja que el guardado
 *          normal persista el resto (el core genera el despacho adicional);
 *   3. pasa las cantidades bajadas al servidor por contexto
 *      (`trixo_adjust_new_qty`) para que el wizard abra con la columna
 *      "Devuelve" ya cargada.
 * La devolucion, la nota de credito y la factura las sigue haciendo el wizard.
 */
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

const ADJUST_BUTTON = "action_open_trixo_adjust";
const QTY_FIELD = "product_uom_qty";
const EPSILON = 1e-9;

patch(FormController.prototype, {
    async beforeExecuteActionButton(clickParams) {
        if (this.props.resModel !== "sale.order" || clickParams.name !== ADJUST_BUTTON) {
            return super.beforeExecuteActionButton(...arguments);
        }
        // El usuario puede apretar el boton con una celda todavia en edicion
        // (bajo la cantidad y no salio del campo). Sin esto, ese valor no esta
        // en el record: el patch no lo ve, el guardado se lleva la cantidad
        // tipeada y el core rechaza el pedido antes de abrir el wizard.
        await this.model._askChanges();
        const root = this.model.root;
        const lines = root.data.order_line?.records || [];
        const reduced = []; // [{ line, resId, original, wanted }]
        for (const line of lines) {
            if (!line.resId || line.data.display_type) {
                continue;
            }
            const original = line._values?.[QTY_FIELD];
            const wanted = line.data[QTY_FIELD];
            if (
                typeof original === "number" &&
                typeof wanted === "number" &&
                wanted < original - EPSILON
            ) {
                reduced.push({ line, resId: line.resId, original, wanted });
            }
        }
        if (!reduced.length) {
            return super.beforeExecuteActionButton(...arguments);
        }

        const reducedIds = new Set(reduced.map((r) => r.resId));
        const changes = await root.getChanges();
        const onlyReductions =
            Object.keys(changes).every((fieldName) => fieldName === "order_line") &&
            (changes.order_line || []).every(
                (command) => command[0] === 1 && reducedIds.has(command[1])
            );

        const newQty = {};
        for (const r of reduced) {
            newQty[r.resId] = r.wanted;
        }
        clickParams.buttonContext = {
            ...(clickParams.buttonContext || {}),
            trixo_adjust_new_qty: newQty,
        };

        if (onlyReductions) {
            // Nada mas que guardar: el pedido no se escribe.
            await root.discard();
            return true;
        }

        // Hay otros cambios (agregados): se restituyen solo las cantidades
        // bajadas y se guarda el resto por el camino estandar.
        for (const r of reduced) {
            await r.line.update({ [QTY_FIELD]: r.original });
        }
        const saved = await super.beforeExecuteActionButton(...arguments);
        if (saved === false) {
            // El guardado fallo: se devuelve al usuario lo que habia tipeado.
            for (const r of reduced) {
                await r.line.update({ [QTY_FIELD]: r.wanted });
            }
        }
        return saved;
    },
});
