/** @odoo-module **/

import { AlignPlugin } from '@html_editor/main/align/align_plugin';
import { patch } from '@web/core/utils/patch';

/**
 * El handler de selectionchange es un listener GLOBAL del documento
 * (SelectionPlugin.addGlobalDomListener). Puede ejecutarse antes de que corra
 * AlignPlugin.setup() -donde se crea this.alignment- o despues del teardown del
 * editor. En ese caso this.alignment es undefined y la asignacion original
 * (this.alignment.displayName = ...) lanza:
 *   TypeError: Cannot set properties of undefined (setting 'displayName')
 *
 * Guardamos contra ese estado: si this.alignment todavia no existe, salimos.
 */
patch(AlignPlugin.prototype, {
    updateAlignmentParams() {
        if (!this.alignment) {
            return;
        }
        return super.updateAlignmentParams(...arguments);
    },
});
