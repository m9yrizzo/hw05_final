from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class TaskCreateFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Harry',
            'last_name': 'Potter',
            'username': 'user_0',
            'email': 'Harry_Potter666@hogwats.uk',
            'password1': 'GaGaGermy_666',
            'password2': 'GaGaGermy_666',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('users:login'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username='user_0',
            ).exists()
        )
