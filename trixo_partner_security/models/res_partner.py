from odoo import models, api, _
from odoo.exceptions import AccessError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        # Add a flag to allow write during creation
        return super(ResPartner, self.with_context(trixo_partner_creation=True)).create(vals_list)

    def write(self, vals):
        # Allow superuser or system calls
        if self.env.is_superuser() or self.env.user._is_system():
            return super().write(vals)

        # Allow writes during creation
        if self.env.context.get('trixo_partner_creation'):
            return super().write(vals)

        # Allow simple internal updates that don't change business data?
        # For "Strict" mode as requested ("de ninguna manera posible"), we block everything
        # unless it is an automated action we explicitly want to allow.
        # But commonly, tracking fields or last_activity might trigger write.
        # Let's start STRICT.
        
        # Check if user has the group
        if not self.env.user.has_group('trixo_partner_security.group_partner_editor'):
             raise AccessError(_("No tienes permiso para editar datos de clientes. Solo puedes crearlos."))

        return super().write(vals)
