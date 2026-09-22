# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from ..tools import FORBIDDEN_UIDS, GROUP_XMLID, ORIGIN_SESSION_KEY

_logger = logging.getLogger(__name__)


class TrxLoginAsUser(models.TransientModel):
    _name = 'trx.login.as.user'
    _description = 'Suplantar usuario (soporte Trixocom)'

    user_id = fields.Many2one(
        'res.users', string='Usuario', required=True,
        domain=lambda self: self._user_domain(),
        help="Usuario cuya sesion se quiere abrir.")
    group_ids = fields.Many2many(
        'res.groups', string='Permisos del usuario',
        compute='_compute_group_ids',
        help="Permisos efectivos del usuario elegido, para saber que va a ver.")

    @api.model
    def _user_domain(self):
        return [('share', '=', False), ('active', '=', True),
                ('id', 'not in', list(FORBIDDEN_UIDS) + [self.env.uid])]

    @api.depends('user_id')
    def _compute_group_ids(self):
        for wiz in self:
            wiz.group_ids = wiz.user_id.sudo().all_group_ids

    def _check_can_switch(self):
        """Verifica en el SERVIDOR que quien llama puede suplantar.

        No alcanza con esconder el boton: este metodo es alcanzable por RPC.
        """
        if not self.env.user.has_group(GROUP_XMLID):
            raise AccessError(_(
                "No tiene permiso para iniciar sesion como otro usuario."))
        if not request:
            raise UserError(_(
                "Esta accion solo puede ejecutarse desde la interfaz web."))

    def action_switch(self):
        self.ensure_one()
        self._check_can_switch()

        session = request.session
        if session.get(ORIGIN_SESSION_KEY):
            raise UserError(_(
                "Ya esta usando la sesion de otro usuario. Vuelva a su usuario "
                "antes de cambiar a otro."))

        target = self.user_id.sudo()
        if not target.exists() or not target.active or target.share \
                or target.id in FORBIDDEN_UIDS or target.id == self.env.uid:
            raise UserError(_("No se puede iniciar sesion como ese usuario."))

        origin = self.env.user
        _logger.warning(
            "TRX LOGIN AS: %s (uid=%s) abre la sesion de %s (uid=%s) "
            "[db=%s ip=%s]",
            origin.login, origin.id, target.login, target.id,
            self.env.cr.dbname, request.httprequest.remote_addr)

        session[ORIGIN_SESSION_KEY] = origin.id
        session['pre_login'] = target.login
        session['pre_uid'] = target.id
        session.finalize(self.env)
        return {'type': 'ir.actions.act_url', 'url': '/odoo', 'target': 'self'}
