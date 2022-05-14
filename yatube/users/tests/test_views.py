from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from ..forms import CreationForm
from http import HTTPStatus


User = get_user_model()


class URL_ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_signup_page_form(self):
        response = self.guest_client.get(reverse('users:signup'))
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIsInstance(form, CreationForm)

    def test_page_accessible_by_name_guest(self):
        templates_url_names = (
            ('users/password_reset_complete.html', (
                'users:password_reset_complete'
            )),
            ('users/password_reset_done.html', 'users:password_reset_done'),
            ('users/password_reset.html', 'users:password_reset'),
            ('users/login.html', 'users:login'),
            ('users/logged_out.html', 'users:logout'),
            ('users/signup.html', 'users:signup'),
        )
        for item in templates_url_names:
            template, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(reverse(url))
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_accessible_by_name_authorized(self):
        templates_url_names = (
            ('users/password_change_done.html', 'users:password_change_done'),
            ('users/password_change.html', 'users:password_change'),
        )
        for item in templates_url_names:
            template, url = item
            with self.subTest(address=url):
                response = self.authorized_client.get(reverse(url))
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
