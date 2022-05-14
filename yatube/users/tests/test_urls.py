from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus


User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.templates_url_names_authorized = (
            ('users/password_change.html', '/auth/password_change/'),
            ('users/password_change_done.html', '/auth/password_change/done/'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес доступен любому пользователю и использует
        соответствующий шаблон.
        """
        templates_url_names = (
            ('users/signup.html', '/auth/signup/'),
            ('users/login.html', '/auth/login/'),
            ('users/logged_out.html', '/auth/logout/'),
            ('users/password_reset.html', '/auth/password_reset/'),
            ('users/password_reset_done.html', '/auth/password_reset/done/'),
            ('users/password_reset_complete.html', '/auth/reset/done/'),
        )
        for item in templates_url_names:
            template, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        for item in self.templates_url_names_authorized:
            with self.subTest(address=item[1]):
                response = self.guest_client.get(item[1], follow=True)
                self.assertRedirects(response, f'/auth/login/?next={item[1]}')

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес доступен авторизованному пользователю и использует
        соответствующий шаблон.
        """
        for item in self.templates_url_names_authorized:
            template, url = item
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
