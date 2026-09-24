import logging

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.tools import format_amount

_logger = logging.getLogger(__name__)

P = "trx_website_distribuidor."
FREE_QTY_DISTRIBUIDOR = 10 ** 12  # "sin límite" para los controles del carrito


class SaleOrder(models.Model):
    _inherit = "sale.order"

    trx_aviso_estado = fields.Selection(
        [("pendiente", "Pendiente"), ("enviado", "Enviado"), ("error", "Con error")],
        string="Aviso de pedido web", copy=False, readonly=True, index=True)
    trx_aviso_log = fields.Text(string="Detalle del aviso", copy=False, readonly=True)

    # ------------------------------------------------------------------ #
    #  Pedido sin stock para distribuidores
    # ------------------------------------------------------------------ #
    def _get_free_qty(self, product):
        if self.env.user._trx_es_distribuidor():
            return FREE_QTY_DISTRIBUIDOR
        return super()._get_free_qty(product)

    # ------------------------------------------------------------------ #
    #  Aviso de pedido
    # ------------------------------------------------------------------ #
    def _trx_param(self, key, default=""):
        return self.env["ir.config_parameter"].sudo().get_param(P + key, default)

    def _trx_debe_avisar(self):
        self.ensure_one()
        if not self.website_id or self.trx_aviso_estado:
            return False
        if self._trx_param("avisar_todos_web", "False") == "True":
            return True
        users = self.partner_id.commercial_partner_id.sudo().with_context(
            active_test=False).user_ids | self.partner_id.sudo().user_ids
        return any(u.has_group(P + "group_distribuidor") for u in users)

    def _trx_encolar_aviso(self):
        pedidos = self.filtered(lambda o: o._trx_debe_avisar())
        if not pedidos:
            return
        pedidos.sudo().write({"trx_aviso_estado": "pendiente"})
        cron = self.env.ref(P + "cron_avisos_pedido", raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()

    def _action_confirm(self):
        res = super()._action_confirm()
        self._trx_encolar_aviso()
        return res

    def _send_payment_succeeded_for_order_mail(self):
        res = super()._send_payment_succeeded_for_order_mail()
        self._trx_encolar_aviso()
        return res

    @api.model
    def _cron_trx_avisar_pedidos(self):
        for order in self.sudo().search([("trx_aviso_estado", "=", "pendiente")], limit=50):
            try:
                with self.env.cr.savepoint():
                    log = order._trx_enviar_aviso()
                order.write({"trx_aviso_estado": "enviado", "trx_aviso_log": log})
            except Exception as err:  # noqa: BLE001
                _logger.exception("Aviso de pedido %s falló", order.name)
                order.write({"trx_aviso_estado": "error",
                             "trx_aviso_log": "%s: %s" % (type(err).__name__, err)})
            self.env.cr.commit()

    def _trx_url(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        return "%s/odoo/sales/%s" % (base.rstrip("/"), self.id)

    def _trx_texto_aviso(self):
        self.ensure_one()
        entrega = self.carrier_id.name or ""
        lineas = len(self.order_line.filtered(lambda l: not l.display_type and not l.is_delivery))
        return (
            "🛒 Nuevo pedido web %s\n"
            "Cliente: %s\n"
            "Total: %s (%s ítems)%s\n"
            "Ver pedido: %s"
        ) % (
            self.name,
            self.partner_id.commercial_partner_id.name or self.partner_id.name,
            format_amount(self.env, self.amount_total, self.currency_id),
            lineas,
            ("\nEntrega: %s" % entrega) if entrega else "",
            self._trx_url(),
        )

    def _trx_enviar_aviso(self):
        self.ensure_one()
        texto = self._trx_texto_aviso()
        titulo = "Nuevo pedido web %s" % self.name
        log = []
        bot = self.env.ref("base.partner_root")
        users = self.env["res.users"].sudo().search([
            ("share", "=", False), ("active", "=", True),
            ("id", "!=", self.env.ref("base.user_root").id)])

        # 1) Notificación a todos los usuarios internos: bandeja/email + push
        #    nativo de Odoo en los dispositivos registrados.
        body = Markup("<br/>").join(escape(t) for t in texto.split("\n"))
        self.sudo().message_post(
            body=body, subject=titulo, author_id=bot.id,
            message_type="comment", subtype_xmlid="mail.mt_comment",
            partner_ids=users.partner_id.ids)
        log.append("Notificación a %s usuarios internos" % len(users))

        # 2) Push de trx_web_push (si está instalado).
        if "trx.web.push.subscription" in self.env:
            try:
                self.env["trx.web.push.subscription"].sudo().send_to_users(
                    users, title=titulo, body=texto.split("\n", 1)[-1],
                    url="/odoo/sales/%s" % self.id)
                log.append("Push trx_web_push enviado")
            except Exception as err:  # noqa: BLE001
                log.append("Push trx_web_push ERROR: %s" % err)

        # 3) WhatsApp.
        log.extend(self._trx_enviar_whatsapp(body, bot))
        return "\n".join(log)

    def _trx_enviar_whatsapp(self, body, bot):
        destinos = [d.strip() for d in (self._trx_param("wa_destinos") or "").split(",") if d.strip()]
        if not destinos:
            return ["WhatsApp: sin destinos configurados"]
        if self._trx_param("wa_activo", "False") != "True":
            return ["WhatsApp DESACTIVADO (modo prueba), no se envió a: %s" % ", ".join(destinos)]
        if "whatsapp.account" not in self.env:
            return ["WhatsApp: módulo trixo_whatsapp no instalado"]
        account = self.env["whatsapp.account"].sudo().search(
            [("provider", "=", "whatsmeow")], limit=1)
        if not account:
            return ["WhatsApp: no hay cuenta whatsmeow"]
        Channel = self.env["discuss.channel"].sudo()
        WaMsg = self.env["whatsapp.message"].sudo()
        log = []
        for dest in destinos:
            try:
                if dest.endswith("@g.us"):
                    channel = Channel._get_or_create_whatsapp_group_channel(account, dest)
                else:
                    channel = Channel._get_or_create_whatsapp_channel(
                        account, dest.split("@")[0].lstrip("+"))
                msg = channel.message_post(
                    body=body, author_id=bot.id,
                    message_type="comment", subtype_xmlid="mail.mt_comment")
                wa = WaMsg.search([("mail_message_id", "=", msg.id)], limit=1)
                estado = wa.state if wa else "sin registro"
                log.append("WhatsApp %s: %s%s" % (
                    dest, estado, (" (%s)" % wa.failure_reason) if wa and wa.failure_reason else ""))
            except Exception as err:  # noqa: BLE001
                log.append("WhatsApp %s ERROR: %s" % (dest, err))
        return log
