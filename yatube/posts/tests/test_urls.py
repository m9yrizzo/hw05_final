from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Post, Group
from http import HTTPStatus


User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
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
            ('posts/index.html', '/'),
            ('posts/group_list.html', f'/group/{self.group.slug}/'),
            ('posts/profile.html', f'/profile/{self.user.username}/'),
            ('posts/post_detail.html', f'/posts/{self.post.id}/'),
        )
        for item in templates_url_names:
            template, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_create_edit_for_autorized(self):
        """URL-адрес создания поста использует соответствующий шаблон."""
        templates_url_names = (
            ('/create/', 'posts/post_create.html'),
            (f'/posts/{self.post.id}/edit/', 'posts/post_create.html'),
        )
        for item in templates_url_names:
            url, template = item
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        templates_url_names = (
            ('/auth/login/?next=/create/', '/create/'),
            (
                f'/auth/login/?next=/posts/{self.post.id}/edit/', (
                    f'/posts/{self.post.id}/edit/'
                )
            ),
        )
        for item in templates_url_names:
            redirect, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_edit_post_redirect_not_author_on_post_detail(self):
        """Страница по адресу /posts/<post_id>/edit/ перенаправит авторизованному
        пользователю не являющимся автором поста на подробную страницу поста.
        """
        user2 = User.objects.create_user(username='auth2')
        authorized_client2 = Client()
        authorized_client2.force_login(user2)
        response = authorized_client2.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            (f'/posts/{self.post.id}/')
        )

    def test_urls_unexisting_page(self):
        """URL-адрес несуществующей страницы вернет ошибку 404.
        """
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
