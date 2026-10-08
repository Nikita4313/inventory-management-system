from django.test import TestCase
from django.test import RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from accounts.views import admin_panel_view


class RegistrationPermissionsTests(TestCase):
	def test_new_accounts_are_viewers_and_cannot_create_products(self):
		response = self.client.post(reverse('accounts:register'), {
			'first_name': 'New',
			'last_name': 'User',
			'username': 'new_viewer',
			'email': 'new_viewer@example.com',
			'password1': 'Tidal!Maple782',
			'password2': 'Tidal!Maple782',
		})

		self.assertEqual(response.status_code, 302)
		user = User.objects.get(username='new_viewer')
		self.assertEqual(user.profile.role, 'viewer')
		self.assertFalse(user.profile.can_edit)
		self.assertFalse(user.profile.can_delete)

		response = self.client.post(reverse('products:product_create'), {})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('products:product_list'))


class AdminPanelAccessTests(TestCase):
	def setUp(self):
		self.request_factory = RequestFactory()
		self.admin_user = User.objects.create_user(username='panel_admin', password='ExamplePass!482')
		self.admin_user.profile.role = 'admin'
		self.admin_user.profile.save()

	def test_admin_role_can_open_panel(self):
		request = self.request_factory.get(reverse('accounts:admin_panel'))
		request.user = self.admin_user

		with patch('accounts.views.render') as render:
			response = admin_panel_view(request)

		self.assertEqual(response, render.return_value)
		render.assert_called_once()
		self.assertEqual(render.call_args.args[1], 'accounts/admin_panel.html')

	def test_viewer_is_redirected_from_panel(self):
		viewer = User.objects.create_user(username='panel_viewer', password='ExamplePass!482')
		request = self.request_factory.get(reverse('accounts:admin_panel'))
		request.user = viewer

		with patch('accounts.views.messages.error'):
			response = admin_panel_view(request)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse('products:dashboard'))
