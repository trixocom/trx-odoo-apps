import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Trixocom - Geo-barrera de Asistencias
 *
 * El systray estandar, cuando no logra obtener la ubicacion, ofrece
 * "Continuar de todos modos" y ficha sin coordenadas. Con geo-barrera
 * exigida eso seria la forma de saltarla, asi que aca se reemplaza ese
 * dialogo por uno informativo sin opcion de continuar. La validacion
 * real igual es del lado del servidor.
 *
 * IMPORTANTE: mantener este archivo 100% ASCII. El minificador de
 * assets de Odoo corrompe el modulo si hay caracteres acentuados
 * (bug visto en produccion 2026-08-30: webclient sin menus).
 */
patch(ActivityMenu.prototype, {
    confirmChecking() {
        if (this.employee && this.employee.geofence_required) {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Ubicacion requerida"),
                body: _t(
                    "No se pudo obtener tu ubicacion. Para registrar el " +
                    "ingreso/egreso permiti el acceso a la ubicacion en tu " +
                    "navegador y ficha desde tu lugar de trabajo."
                ),
                confirmLabel: _t("Entendido"),
                confirm: () => {
                    this._attendanceInProgress = false;ttendanceInProgre},
                dismiss: () => {
                    this._attendanceInProgress = false;ttendanceInProgre},
            });ttendanceInPrreturn;ttendance}
        return super.confirmChecking();ttend},
});t