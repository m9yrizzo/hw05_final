import shutil
import tempfile
from datetime import datetime
from http import HTTPStatus
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Post, Group, Follow


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
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

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'author': self.user.username,
            'pub_date': datetime.now(),
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                group_id=self.group.id,
                text='Тестовый текст',
                author=self.user.id,
            ).exists()
        )
        # Забираем из базы пост, сверяем каждое поле
        test_post = Post.objects.get(id=1)
        self.assertEqual(test_post.text, form_data['text'])
        self.assertEqual(test_post.author.username, form_data['author'])
        self.assertEqual(test_post.group.id, form_data['group'])
        self.assertEqual(test_post.image, 'posts/small.gif')

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        form_data = {
            'text': 'Тестовый пост обновленный',
            'group': group2.id,
            'author': self.user.username,
            'pub_date': datetime.now(),
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        # Проверяем, что создалась запись с заданным слагом
        self.assertTrue(
            Post.objects.filter(
                group_id=group2.id,
                text='Тестовый пост обновленный',
                author=self.user.id,
            ).exists()
        )
        # Забираем из базы пост, сверяем каждое поле
        test_post = Post.objects.get(id=1)
        self.assertEqual(test_post.text, form_data['text'])
        self.assertEqual(test_post.author.username, form_data['author'])
        self.assertEqual(test_post.group.id, form_data['group'])

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group
        )
        comments_count = post.comments.count()
        form_data = {
            'text': 'Новый комментарий',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertEqual(post.comments.count(), comments_count + 1)
        # Забираем из базы пост, сверяем каждое поле
        test_comment = post.comments.get(id=1)
        self.assertEqual(test_comment.text, form_data['text'])
        self.assertEqual(test_comment.author, self.user)
        self.assertEqual(test_comment.post_id, post.id)

        # Комментировать может только зарегистрированный пользователь
        response = self.guest_client.get(
            reverse('posts:add_comment', kwargs={'post_id': post.id})
        )
        first_part_reverse = reverse('users:login')
        second_part_reverse = reverse(
            'posts:add_comment', kwargs={'post_id': post.id}
        )
        self.assertRedirects(
            response, f'{first_part_reverse}?next={second_part_reverse}'
        )

    def test_postlist_for_follows_notfollows(self):
        Follow.objects.create(user=self.user2, author=self.user)
        posts2 = Post.objects.filter(
            author__following__user=self.user2
        ).count()
        posts = Post.objects.filter(author__following__user=self.user).count()
        # добавляем в БД пост от user
        following_post = Post.objects.create(
            # если ставить здесь user2 изначальная логика теста будет провалена
            author=self.user,
            text='Тестовый пост для проверки подписок',
            group=self.group
        )
        posts2_new = Post.objects.filter(
            author__following__user=self.user2
        ).count()
        posts_new = Post.objects.filter(
            author__following__user=self.user
        ).count()

        self.assertEqual(posts2_new, posts2 + 1)
        self.assertEqual(posts_new, posts)

        response = self.authorized_client2.get(
            reverse('posts:follow_index'),
            follow=True
        )
        post_object = response.context['page_obj'][0]
        self.assertEqual(post_object.author, following_post.author)
        self.assertEqual(post_object.group.slug, following_post.group.slug)
        self.assertEqual(post_object.pub_date, following_post.pub_date)
        self.assertEqual(post_object.text, following_post.text)

    def test_follow(self):
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user2.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_unfollow(self):
        Follow.objects.create(user=self.user, author=self.user2)
        follows_count = Follow.objects.count()
        response = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user2.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follows_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_follow_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /follow/ or /unfollow/ перенаправит анонимного
        пользователя на страницу логина.
        """
        templates_url_names = (
            (
                f'/profile/{self.user.username}/',
                f'/auth/login/?next=/profile/{self.user.username}/follow/',
                f'/profile/{self.user.username}/follow/'
            ),
            (
                f'/profile/{self.user.username}/',
                f'/auth/login/?next=/profile/{self.user.username}/unfollow/',
                f'/profile/{self.user.username}/unfollow/'
            ),
        )
        for item in templates_url_names:
            redirect_right, redirect, url = item
            with self.subTest(address=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)
                response2 = self.authorized_client.get(url, follow=True)
                self.assertRedirects(response2, redirect_right)
