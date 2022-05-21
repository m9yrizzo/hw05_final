import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from ..forms import PostForm
from ..models import Post, Group
from datetime import datetime
from http import HTTPStatus


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POST_PER_PAGE = settings.POST_PER_PAGE
POST_ON_SECOND_PAGE = 2
POST_COUNT = 11


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 0',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def post_asserts(cls_1, post_object):
        cls_1.assertEqual(post_object.author, cls_1.user)
        cls_1.assertEqual(post_object.group.slug, cls_1.group.slug)
        cls_1.assertEqual(post_object.pub_date, cls_1.post.pub_date)
        cls_1.assertEqual(post_object.text, cls_1.post.text)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = (
            ('posts/index.html', reverse('posts:main_page')),
            (
                'posts/group_list.html',
                reverse(
                    'posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}
                )
            ),
            (
                'posts/profile.html',
                reverse(
                    'posts:profile',
                    kwargs={'username': f'{self.user.username}'}
                )
            ),
            (
                'posts/post_detail.html',
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}
                )
            )
        )
        for item in templates_pages_names:
            template, name = item
            with self.subTest(reverse_name=name):
                response = self.guest_client.get(name)
                self.assertTemplateUsed(response, template)

        templates_pages_names2 = (
            ('posts/post_create.html', reverse('posts:post_create')),
            (
                'posts/post_create.html',
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'}
                )
            ),
        )
        for item in templates_pages_names2:
            template, name = item
            with self.subTest(reverse_name=name):
                response = self.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_page_show_correct_context(self):
        """Шаблон main_page сформирован с правильным контекстом."""
        templates = (
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for url in templates:
            cache.clear()
            response = self.authorized_client.get(url)
            first_object = response.context['page_obj'][0]
            self.post_asserts(first_object)

    def test_z_image_in_context(self):
        """Шаблон main_page сформирован с правильным контекстом."""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            content_type='image/gif'
        )
        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост c картинкой',
            group=self.group,
            image=uploaded
        )
        templates = (
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:post_detail', kwargs={'post_id': post2.id})
        )
        for item in templates:
            cache.clear()
            response = self.authorized_client.get(item)
            if (item == reverse(
                'posts:post_detail',
                kwargs={'post_id': post2.id}
            )):
                first_object = response.context['post']
            else:
                first_object = response.context['page_obj'][0]
            self.assertEqual(first_object.image, post2.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        second_object = response.context['post']
        self.post_asserts(second_object)
        self.assertEqual(response.context['can_edit'], True)

    def test_post_create_edit_show_correct_context(self):
        templates_pages_names = (
            (reverse('posts:post_create'), False),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ), True),
        )
        for item in templates_pages_names:
            reverse_name, can_edit = item
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                form = response.context.get('form')
                is_edit = response.context.get('is_edit')
                self.assertEqual(is_edit, can_edit)
                self.assertIsNotNone(form)
                self.assertIsInstance(form, PostForm)

    def test_page_contains_number_of_records(self):
        Post.objects.bulk_create(
            [
                Post(
                    author=self.user,
                    text=f'Тестовый пост {pk}',
                    group=self.group,
                    pub_date=datetime.now(),
                ) for pk in range(POST_COUNT)
            ]
        )
        templates_extentions = (
            ({}, POST_PER_PAGE),
            ({'page': 2, }, POST_ON_SECOND_PAGE)
        )
        templates_pages_names = (
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        for item2 in templates_pages_names:
            for item1 in templates_extentions:
                with self.subTest(reverse_name=item2):
                    cache.clear()
                    response = self.authorized_client.get(item2, item1[0])
                    self.assertEqual(
                        len(response.context['page_obj']), item1[1]
                    )

    def test_for_post_creation(self):
        post_ex = Post.objects.create(
            author=self.user,
            text='Тестовый пост для дополнительного тестирования',
            group=self.group2
        )
        templates_pages_names = (
            reverse('posts:main_page'),
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        # Проверка добавления нового поста на страницу
        for item in templates_pages_names:
            cache.clear()
            response = self.authorized_client.get(item)
            self.assertEqual(
                response.context['page_obj'][0].author.username,
                post_ex.author.username
            )
            self.assertEqual(
                response.context['page_obj'][0].text,
                post_ex.text
            )
            self.assertEqual(
                response.context['page_obj'][0].group,
                post_ex.group
            )
        # Проверка отсутствия нового поста на странице чужой группы
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertNotEqual(
            response.context['page_obj'][0].group,
            post_ex.group
        )

    def test_cash(self):
        """Проверка кэша страницы index"""
        response_1 = self.authorized_client.get(reverse("posts:main_page"))
        Post.objects.get(id=self.post.id).delete()
        response_2 = self.authorized_client.get(reverse("posts:main_page"))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse("posts:main_page"))
        self.assertNotEqual(response_1.content, response_3.content)
