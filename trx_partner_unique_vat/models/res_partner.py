# -*- coding: utf-8 -*-
import logging

from odoo import _, api, models
from odoo.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _trx_get_duplicate_vat_partner(self):
        """Devuelve el primer partner (distinto de self) que comparte el mismo
        CUIT, o un recordset vacio si no hay duplicado.

        Solo se controla cuando el tipo de identificacion es CUIT (codigo AFIP
        '80'); para DNI, CF u otros documentos no se aplica unicidad porque es
        normal que se repitan (por ejemplo "Consumidor Final").

        La comparacion se hace sobre el CUIT compacto (``l10n_ar_vat``), el
        valor canonico que normaliza la localizacion argentina, de modo que
        ``20-12345678-9`` y ``20123456789`` se consideran el mismo numero.
        """
        self.ensure_one()
        cuit = self.l10n_ar_vat
        if not cuit:
            return self.browse()

        try:
            import stdnum.ar.cuit
            formatted = stdnum.ar.cuit.format(cuit)
        except Exception:  # pragma: no cover - defensivo
            formatted = cuit

        domain = [
            ('id', '!=', self.id),
            ('parent_id', '=', False),
            ('company_id', 'in', [False] + self.company_id.ids),
            '|', ('vat', '=', cuit), ('vat', '=', formatted),
        ]
        # Incluye partners archivados: un CUIT duplicado en un contacto
        # archivado tambien debe avisarse (se puede desarchivar).
        candidates = self.with_context(active_test=False).search(domain)
        return candidates.filtered(lambda p: p.l10n_ar_vat == cuit)[:1]

    @api.constrains('vat', 'parent_id', 'l10n_latam_identification_type_id', 'company_id')
    def _trx_check_unique_vat(self):
        # Permite saltear el control en procesos masivos (migraciones,
        # importaciones) cuando se setea el contexto trx_skip_unique_vat.
        if self.env.context.get('trx_skip_unique_vat'):
            return

        for partner in self:
            # Excepcion pedida: un contacto que cuelga de una empresa
            # (parent_id seteado) puede compartir el CUIT de su empresa.
            if partner.parent_id:
                continue

            original = partner._trx_get_duplicate_vat_partner()
            if not original:
                continue

            archived = _(' (archivado)') if not original.active else ''
            message = _(
                'Ya existe un contacto con el mismo CUIT %(vat)s:\n\n'
                '    %(name)s%(archived)s\n\n'
                'No se puede crear ni guardar otro contacto con ese CUIT. '
                'Use el contacto existente, o si se trata de una persona de '
                'esa empresa, carguela como contacto dependiente de la misma.',
                vat=original.l10n_ar_formatted_vat or original.vat,
                name=original.display_name,
                archived=archived,
            )

            view_id = self.env.ref('base.view_partner_form').id
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': original.id,
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'current',
                'context': {'create': False},
            }
            raise RedirectWarning(message, action, _('Ver el contacto original'))
