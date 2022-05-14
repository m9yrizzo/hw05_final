from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class URL_ViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_page(self):
        templates_url_names = (
            ('about/author.html', '/about/author/'),
            ('about/tech.html', '/about/tech/'),
        )
        for item in templates_url_names:
            template, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени, доступен."""
        templates_namespace_names = (
            ('about/author.html', 'about:author'),
            ('about/tech.html', 'about:tech'),
        )
        for item in templates_namespace_names:
            template, name = item
            with self.subTest(address=name):
                response = self.guest_client.get(reverse(name))
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
