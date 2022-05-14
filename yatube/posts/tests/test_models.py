from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )

    def test_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        task_group = PostModelTest.group
        task_post = PostModelTest.post

        fields = (
            (task_post, task_post.text[:15]),
            (task_group, f'Сообщество: {task_group.title}'),
        )
        for item in fields:
            model, testing_str = item
            with self.subTest(field=model):
                self.assertEqual(model.__str__(), testing_str)

    def test_verbose_names(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task_post = PostModelTest.post
        field_verboses = (
            ('text', 'Текст поста'),
            ('author', 'Автор'),
            ('group', 'Сообщество'),
        )
        for item in field_verboses:
            model_field, testing_verbose_name = item
            with self.subTest(field=model_field):
                self.assertEqual(
                    task_post._meta.get_field(model_field).verbose_name,
                    testing_verbose_name
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        task_post = PostModelTest.post
        field_help_texts = (
            ('text', 'Текст нового поста'),
            ('group', 'Группа, к которой будет относиться пост'),
        )
        for item in field_help_texts:
            model_field, testing_help_text = item
            with self.subTest(field=model_field):
                self.assertEqual(
                    task_post._meta.get_field(model_field).help_text,
                    testing_help_text
                )
