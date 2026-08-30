import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Trixocom - Geo-barrera de Asistencias
 *
 * El systray estándar, cuando no logra obtener la ubicación, ofrece
 * "Continuar de todos modos" y ficha sin coordenadas. Con geo-barrera
 * exigida eso sería la forma de saltarla, así que acá se reemplaza ese
 * diálogo por uno informativo sin opción de continuar. La validación
 * real igual es del lado del servidor.
 */
patch(ActivityMenu.prototype, {
    confirmChecking() {
        if (this.employee && this.employee.geofence_required) {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Ubicación requerida"),
                body: _t(
                    "No se pudo obtener tu ubicación. Para registrar el " +
                    "ingreso/egreso permití el acceso a la ubicación en tu " +
                    "navegador y fichá desde tu lugar de trabajo."
                ),
                confirmLabel: _t("Entendido"),
                confirm: () => {
                    this._attendanceInProgress = false;
                },
                dismiss: () => {
                    this._attendanceInProgress = false;
                },
            });
            return;
        }
        return super.confirmChecking();
    },
});
