from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Поклонники',
            slug='Fan',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовый пост',
            group=PostsURLTest.group
        )
        cls.exists_url_open_users = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}': HTTPStatus.OK,
            f'/profile/{cls.post.author}': HTTPStatus.OK,
            f'/posts/{cls.post.pk}': HTTPStatus.OK,
            '/Unexisting_page/': HTTPStatus.NOT_FOUND
        }
        cls.templates_of_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_to_all_users(self):
        """Проверка доступности страниц неавторизированным пользователям"""
        for address, http_status in PostsURLTest.exists_url_open_users.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(response.status_code, http_status)

    def test_url_create_and_edit_post_auth(self):
        """Проверка доступа авторизированным пользователям"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get('/posts'
                                              f'/{PostsURLTest.post.pk}'
                                              '/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates_of_urls_app_posts(self):
        """Проверка соответствия шаблонов"""
        for address, template in PostsURLTest.templates_of_urls.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
