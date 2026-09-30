# -*- coding: utf-8 -*-
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_ar.tests.common import TestArCommon


@tagged("post_install_l10n", "post_install", "-at_install")
class TestFiscalVatGuard(TestArCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls._create_journal("preprinted")
        cls.partner = cls.res_partner_adhoc
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")

        # Posiciones fiscales armadas igual que en produccion:
        #   "NF"   reemplaza IVA 21% -> IVA 0%
        #   "AFIP" reemplaza IVA 0%  -> IVA 21%
        cls.tax_0.active = True
        fiscal_position = cls.env["account.fiscal.position"]
        cls.fp_nf = fiscal_position.create({"name": "NF (test)"})
        cls.fp_afip = fiscal_position.create({"name": "AFIP (test)"})
        cls.tax_0.write({
            "fiscal_position_ids": [Command.link(cls.fp_nf.id)],
            "original_tax_ids": [Command.link(cls.tax_21.id)],
        })
        cls.tax_21.write({
            "fiscal_position_ids": [Command.link(cls.fp_afip.id)],
            "original_tax_ids": [Command.link(cls.tax_0.id)],
        })

    # ------------------------------------------------------------------
    # Pedido de venta: los impuestos siguen a la posicion fiscal
    # ------------------------------------------------------------------
    def _new_order(self, fiscal_position):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "fiscal_position_id": fiscal_position.id,
            "order_line": [Command.create({
                "product_id": self.product_iva_21.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
            })],
        })

    def test_01_order_taxes_follow_fiscal_position(self):
        order = self._new_order(self.fp_nf)
        line = order.order_line
        self.assertEqual(line.tax_ids, self.tax_0, "con NF la linea nace en IVA 0%")

        order.fiscal_position_id = self.fp_afip
        self.assertEqual(
            line.tax_ids, self.tax_21,
            "al pasar a la posicion fiscal AFIP la linea tiene que quedar en IVA 21%",
        )
        self.assertEqual(line.price_unit, 100.0, "el precio unitario no se toca")

        order.fiscal_position_id = self.fp_nf
        self.assertEqual(line.tax_ids, self.tax_0, "y al volver a NF, otra vez IVA 0%")
        self.assertEqual(line.price_unit, 100.0)

    def test_02_order_form_onchange(self):
        order = self._new_order(self.fp_nf)
        with Form(order) as form:
            form.fiscal_position_id = self.fp_afip
        self.assertEqual(order.order_line.tax_ids, self.tax_21)

    def test_03_order_to_invoice(self):
        """El caso real: pedido no fiscal al que se le cambia la posicion
        fiscal y se factura. La factura tiene que salir con IVA 21%."""
        order = self._new_order(self.fp_nf)
        order.fiscal_position_id = self.fp_afip
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(invoice.invoice_line_ids.tax_ids, self.tax_21)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertTrue(invoice.amount_tax > 0)

    # ------------------------------------------------------------------
    # Factura fiscal: no se valida con IVA 0%
    # ------------------------------------------------------------------
    def _new_invoice(self, tax, **kwargs):
        return self._create_invoice_ar(
            invoice_line_ids=[self._prepare_invoice_line(
                price_unit=100, product_id=self.product_iva_21, tax_ids=tax,
            )],
            **kwargs,
        )

    def test_10_invoice_vat_zero_is_blocked(self):
        invoice = self._new_invoice(self.tax_0)
        self.assertTrue(invoice.journal_id.l10n_latam_use_documents)
        with self.assertRaisesRegex(UserError, "IVA 0%"):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")
        self.assertFalse(invoice.posted_before)

    def test_11_invoice_vat_21_posts(self):
        invoice = self._new_invoice(self.tax_21)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_12_journal_can_allow_vat_zero(self):
        self.journal.trx_allow_vat_zero = True
        invoice = self._new_invoice(self.tax_0)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_13_credit_note_vat_zero_is_not_blocked(self):
        """Las NC con IVA 0% tienen que poder emitirse para anular facturas
        que ya salieron con IVA 0%."""
        refund = self._new_invoice(self.tax_0, move_type="out_refund")
        refund.action_post()
        self.assertEqual(refund.state, "posted")

    def test_14_journal_without_documents_is_not_blocked(self):
        journal = self.env["account.journal"].create({
            "name": "Pedido NF (test)",
            "type": "sale",
            "code": "NFT",
            "l10n_latam_use_documents": False,
            "company_id": self.env.company.id,
        })
        invoice = self._new_invoice(self.tax_0, journal_id=journal.id)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
