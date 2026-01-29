from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestPartnerSecurity(TransactionCase):

    def setUp(self):
        super(TestPartnerSecurity, self).setUp()
        
        # Groups
        self.group_creator = self.env.ref('trixo_partner_security.group_partner_creator')
        self.group_editor = self.env.ref('trixo_partner_security.group_partner_editor')

        # 1. Read Only User (No special groups)
        self.user_readonly = self.env['res.users'].create({
            'name': 'Read Only User',
            'login': 'user_readonly',
            'email': 'readonly@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        # 2. Creator User (Only Creator group)
        self.user_creator = self.env['res.users'].create({
            'name': 'Creator User',
            'login': 'user_creator',
            'email': 'creator@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.group_creator.id])]
        })

        # 3. Editor User (Editor group - implies Creator)
        self.user_editor = self.env['res.users'].create({
            'name': 'Editor User',
            'login': 'user_editor',
            'email': 'editor@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.group_editor.id])]
        })

    def test_readonly_user(self):
        """Test Read Only user: Cannot Create, Cannot Edit."""
        # Try Create
        with self.assertRaises(AccessError, msg="Read-only user should not be able to create"):
            self.env['res.partner'].with_user(self.user_readonly).create({'name': 'Fail Create'})
            
        # Try Edit (existing partner)
        partner = self.env['res.partner'].create({'name': 'Existing Partner'})
        with self.assertRaises(AccessError, msg="Read-only user should not be able to edit"):
             partner.with_user(self.user_readonly).write({'name': 'Fail Write'})

    def test_creator_user(self):
        """Test Creator user: Can Create, Cannot Edit."""
        # Try Create
        partner = self.env['res.partner'].with_user(self.user_creator).create({'name': 'Success Create'})
        self.assertTrue(partner.id, "Creator user should be able to create")
        
        # Try Edit (the one they just created - should fail based on requirements "no editar", assuming Strict)
        # Requirement: "indicar que usuarios pueden crear y no editar"
        # My implementation allows write *during* creation, but verify separate write fails.
        with self.assertRaises(AccessError, msg="Creator user should not be able to edit existing"):
             partner.with_user(self.user_creator).write({'name': 'Fail Write'})

    def test_editor_user(self):
        """Test Editor user: Can Create, Can Edit."""
        # Try Create
        partner = self.env['res.partner'].with_user(self.user_editor).create({'name': 'Editor Create'})
        self.assertTrue(partner.id, "Editor user should be able to create")
        
        # Try Edit
        partner.with_user(self.user_editor).write({'name': 'Success Write'})
        self.assertEqual(partner.name, 'Success Write', "Editor user should be able to edit")
