# -*- coding: utf-8 -*-
from odoo import api, models, tools

from .ir_rule import GROUP_XMLID

#: Apps (menús raíz) que ve un vendedor restringido. Todo lo demás se oculta.
ALLOWED_ROOT_MENUS = (
    'crm.crm_menu_root',
)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user._get_group_ids())', 'debug')
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug=debug)
        if not self.env.user.has_group(GROUP_XMLID):
            return visible
        allowed_roots = set()
        for xmlid in ALLOWED_ROOT_MENUS:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                allowed_roots.add(menu.id)
        keep = set()
        for menu in self.sudo().browse(visible):
            root_id = int((menu.parent_path or '%s/' % menu.id).split('/')[0])
            if root_id in allowed_roots:
                keep.add(menu.id)
        return frozenset(keep)
