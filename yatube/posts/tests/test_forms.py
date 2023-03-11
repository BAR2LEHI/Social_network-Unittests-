from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class FormsPostTest(TestCase):
    """Тестирование форм"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text='Текстовый пост',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FormsPostTest.user)

    def test_post_create_if_form_valid(self):
        """Проверка формы создания поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост',
            'author': f'{FormsPostTest.user}'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': FormsPostTest.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=f'{FormsPostTest.user.pk}'
            ).exists()
        )

    def test_post_edit_if_form_valid(self):
        """Проверка формы редактирования поста"""
        old_post = Post.objects.create(
            text='Оригинал',
            author=FormsPostTest.user
        )
        form_data = {
            'text': 'Копия'
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': old_post.pk}))
        edit_post = Post.objects.get(pk=old_post.pk)
        self.assertEqual(edit_post.text, form_data['text'])
