# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

GROUP_XMLID = 'trx_crm_restricted_salesman.group_restricted_salesman'

#: (sufijo xmlid, modelo, dominio para el vendedor restringido)
#: Cada regla es GLOBAL (se suma con AND a todo lo demás) y sólo restringe a
#: los miembros del grupo: para el resto de los usuarios el dominio es [] (sin
#: restricción). Los modelos que no existan en la base se saltean (p.ej.
#: trx.voip.call si trx_voip no está instalado).
RULES = [
    # --- CRM / Ventas: sólo lo propio (no lo "sin asignar") -----------------
    ('crm_lead', 'crm.lead',
     "[('user_id', '=', user.id)]"),
    ('crm_activity_report', 'crm.activity.report',
     "[('user_id', '=', user.id)]"),
    ('sale_order', 'sale.order',
     "[('user_id', '=', user.id)]"),
    ('sale_order_line', 'sale.order.line',
     "[('salesman_id', '=', user.id)]"),
    ('sale_report', 'sale.report',
     "[('user_id', '=', user.id)]"),
    # --- Facturación / pagos: sólo lo que sale de sus propios pedidos -------
    ('account_move', 'account.move',
     "[('invoice_user_id', '=', user.id)]"),
    ('account_move_line', 'account.move.line',
     "[('move_id.invoice_user_id', '=', user.id)]"),
    ('account_invoice_report', 'account.invoice.report',
     "[('invoice_user_id', '=', user.id)]"),
    ('payment_transaction', 'payment.transaction',
     "[('sale_order_ids.user_id', '=', user.id)]"),
    ('payment_token', 'payment.token',
     "[(0, '=', 1)]"),
    # --- Contactos: los suyos + usuarios internos/compañías propias ---------
    ('res_partner', 'res.partner',
     "['|', '|', '|', '|', '|', '|', '|',"
     " ('partner_share', '=', False),"
     " ('id', 'in', user.company_ids.partner_id.ids),"
     " ('create_uid', '=', user.id),"
     " ('user_id', '=', user.id),"
     " ('commercial_partner_id.create_uid', '=', user.id),"
     " ('commercial_partner_id.user_id', '=', user.id),"
     " ('commercial_partner_id.opportunity_ids.user_id', '=', user.id),"
     " ('commercial_partner_id.sale_order_ids.user_id', '=', user.id)]"),
    ('res_partner_bank', 'res.partner.bank',
     "[(0, '=', 1)]"),
    # --- Productos y listas de precios: sólo los habilitados ----------------
    ('product_template', 'product.template',
     "[('trx_restricted_visible', '=', True)]"),
    ('product_product', 'product.product',
     "[('product_tmpl_id.trx_restricted_visible', '=', True)]"),
    ('product_pricelist', 'product.pricelist',
     "[('trx_restricted_visible', '=', True)]"),
    ('product_pricelist_item', 'product.pricelist.item',
     "[('pricelist_id.trx_restricted_visible', '=', True)]"),
    ('product_supplierinfo', 'product.supplierinfo',
     "[(0, '=', 1)]"),
    # --- Conversaciones: sólo canales de los que es miembro -----------------
    #     (los grupos de WhatsApp son canales públicos para todo interno)
    ('discuss_channel', 'discuss.channel',
     "['|', ('is_member', '=', True), ('parent_channel_id.is_member', '=', True)]"),
    # --- Calendario: sólo sus eventos --------------------------------------
    ('calendar_event', 'calendar.event',
     "['|', ('user_id', '=', user.id), ('partner_ids', 'in', [user.partner_id.id])]"),
    # --- Proyectos / tareas: sólo lo que sigue o tiene asignado -------------
    ('project_project', 'project.project',
     "['|', ('user_id', '=', user.id), ('message_partner_ids', 'in', [user.partner_id.id])]"),
    ('project_task', 'project.task',
     "['|', ('user_ids', 'in', user.id), ('message_partner_ids', 'in', [user.partner_id.id])]"),
    ('project_milestone', 'project.milestone',
     "[('project_id.message_partner_ids', 'in', [user.partner_id.id])]"),
    ('project_update', 'project.update',
     "[('project_id.message_partner_ids', 'in', [user.partner_id.id])]"),
    # --- Otros ---------------------------------------------------------------
    ('spreadsheet_dashboard', 'spreadsheet.dashboard',
     "[(0, '=', 1)]"),
    ('hr_employee_public', 'hr.employee.public',
     "[('user_id', '=', user.id)]"),
    ('trx_voip_call', 'trx.voip.call',
     "[('user_id', '=', user.id)]"),
]


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def _trx_restricted_salesman_sync_rules(self):
        """Crea/actualiza las reglas globales de RULES con xmlid del módulo."""
        data_list = []
        for suffix, model_name, domain in RULES:
            model = self.env['ir.model']._get(model_name)
            if not model:
                _logger.info("trx_crm_restricted_salesman: modelo %s no "
                             "instalado, se omite su regla", model_name)
                continue
            data_list.append({
                'xml_id': 'trx_crm_restricted_salesman.rule_rs_%s' % suffix,
                'noupdate': False,
                'values': {
                    'name': 'Vendedor restringido: %s' % model_name,
                    'model_id': model.id,
                    'groups': [(5, 0, 0)],
                    'domain_force': "(%s) if user.has_group('%s') else []"
                                    % (domain, GROUP_XMLID),
                    'perm_read': True,
                    'perm_write': True,
                    'perm_create': True,
                    'perm_unlink': True,
                    'active': True,
                },
            })
        self.sudo()._load_records(data_list, update=True)
        return True
