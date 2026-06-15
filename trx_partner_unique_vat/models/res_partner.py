# -*- coding: utf-8 -*-
import logging

from odoo import _, api, models

from odoo.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)

# Codigo AFIP del tipo de documento "Sin identificar / venta global diaria"
# (Consumidor Final). Es el unico documento que se repite legitimamente.
AFIP_CODE_UNIDENTIFIED = '99'
# Codigo AFIP del CUIT (para usar el valor compacto canonico de la localizacion).
AFIP_CODE_CUIT = '80'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _trx_vat_unique_key(self):
        """Devuelve (tipo_documento, valor_normalizado) cuando el documento del
        contacto debe ser unico, o (recordset vacio, '') cuando no corresponde
        controlarlo.

        No se controla cuando:
          * no hay ``vat`` o no hay tipo de identificacion;
          * el tipo es "Sin identificar / venta global diaria" (codigo AFIP
            ``99`` = Consumidor Final), que es normal que se repita.

        Para CUIT (codigo ``80``) se usa el valor compacto de la localizacion
        (``l10n_ar_vat``). Para el resto (DNI, CUIL, Pasaporte, etc.) se
        normaliza el ``vat`` quitando separadores, de modo que ``12.345.678`` y
        ``12345678`` se consideran el mismo documento. La comparacion siempre se
        hace DENTRO del mismo tipo de documento, asi un DNI no colisiona con un
        CUIT que contenga los mismos digitos.
        """
        self.ensure_one()
        empty = self.env['l10n_latam.identification.type'].browse()
        id_type = self.l10n_latam_identification_type_id
        if not self.vat or not id_type:
            return empty, ''
        if id_type.l10n_ar_afip_code == AFIP_CODE_UNIDENTIFIED:
            return empty, ''

        if id_type.l10n_ar_afip_code == AFIP_CODE_CUIT and self.l10n_ar_vat:
            normalized = self.l10n_ar_vat
        else:
            normalized = ''.join(c for c in self.vat.upper() if c.isalnum())

        if not normalized:
            return empty, ''
        return id_type, normalized

    def _trx_get_duplicate_vat_partner(self):
        """Primer partner (distinto de self) con el mismo documento, o un
        recordset vacio si no hay duplicado."""
        self.ensure_one()
        id_type, key = self._trx_vat_unique_key()
        if not id_type:
            return self.browse()

        domain = [
            ('id', '!=', self.id),
            ('parent_id', '=', False),
            ('company_id', 'in', [False] + self.company_id.ids),
            ('l10n_latam_identification_type_id', '=', id_type.id),
            ('vat', '!=', False),
        ]
        # Incluye contactos archivados: un documento duplicado en un contacto
        # archivado tambien debe avisarse (se puede desarchivar).
        candidates = self.with_context(active_test=False).search(domain)
        return candidates.filtered(
            lambda p: p._trx_vat_unique_key()[1] == key
        )[:1]

    @api.constrains('vat', 'parent_id', 'l10n_latam_identification_type_id', 'company_id')
    def _trx_check_unique_vat(self):
        # Permite saltear el control en procesos masivos (migraciones,
        # importaciones) seteando el contexto trx_skip_unique_vat.
        if self.env.context.get('trx_skip_unique_vat'):
            return

        for partner in self:
            # Excepcion pedida: un contacto que cuelga de una empresa
            # (parent_id seteado) puede compartir el documento de su empresa.
            if partner.parent_id:
                continue

            original = partner._trx_get_duplicate_vat_partner()
            if not original:
                continue

            doc_label = original.l10n_latam_identification_type_id.display_name or _('documento')
            doc_value = original.l10n_ar_formatted_vat or original.vat
            archived = _(' (archivado)') if not original.active else ''
            message = _(
                'Ya existe un contacto con el mismo %(doc)s %(vat)s:\n\n'
                '    %(name)s%(archived)s\n\n'
                'No se puede crear ni guardar otro contacto con ese %(doc)s. '
                'Use el contacto existente, o si se trata de una persona de '
                'esa empresa, carguela como contacto dependiente de la misma.',
                doc=doc_label,
                vat=doc_value,
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
