from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestPartnerSecurity(TransactionCase):

    def setUp(self):
        super(TestPartnerSecurity, self).setUp()
        # Create a user without the 'group_partner_editor' group
        self.user_restricted = self.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_user',
            'email': 'restricted@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        # Ensure they don't have the editor group
        group_editor = self.env.ref('trixo_partner_security.group_partner_editor')
        self.user_restricted.groups_id = [(3, group_editor.id)]

    def test_create_partner(self):
        """Test that a restricted user can create a partner."""
        partner = self.env['res.partner'].with_user(self.user_restricted).create({
            'name': 'New Customer',
            'email': 'customer@example.com',
        })
        self.assertTrue(partner.id, "Partner should be created successfully")

    def test_write_partner(self):
        """Test that a restricted user cannot edit a partner."""
        # First create as superuser/admin so we have a partner to edit
        partner = self.env['res.partner'].create({
            'name': 'Existing Customer',
        })

        # Try to write as restricted user
        with self.assertRaises(AccessError):
            partner.with_user(self.user_restricted).write({
                'name': 'Modified Name'
            })
