import shutil
import tempfile
from time import sleep

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    """Тесты view-функций приложения posts"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x02'
        )
        cls.image_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_2 = SimpleUploadedFile(
            name='image2.gif',
            content=cls.image_2,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Поклонники',
            slug='Fan',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовый пост',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Второй текстовый пост',
            group=cls.group
        )
        cls.post_3 = Post.objects.create(
            author=cls.user,
            text='Третий текстовый пост',
            group=cls.group
        )
        # Я понимаю, как это ужасно выглядит, но по-другому проблему
        # с тестом test_post_image_context решить не смог,
        # помощь в пачке не спасла, прошу совет:(
        sleep(0.5)
        cls.post_img = Post.objects.create(
            author=cls.user,
            text='Пост с картинкой',
            group=cls.group,
            image=cls.uploaded_2
        )
        cls.template_and_page = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': cls.post.author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': cls.post.pk}
                    ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': cls.post.pk}
                    ): 'posts/create_post.html'
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """Страницы используют корректные шаблоны"""
        for reverse_name, template in PostsPagesTest.template_and_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Проверка контекста главной страницы"""
        response = self.guest_client.get(reverse('posts:index'))
        home_posts = response.context['page_obj']
        self.assertIn(PostsPagesTest.post, home_posts)
        self.assertIn(PostsPagesTest.post_2, home_posts)
        self.assertIn(PostsPagesTest.post_3, home_posts)

    def test_group_list_page_show_correct_context(self):
        """Проверка контекста страницы группы"""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.group.slug}
            )
        )
        post_0 = response.context['page_obj'][0]
        post_1 = response.context['page_obj'][1]
        post_group_0 = post_0.group.title
        post_group_1 = post_1.group.title
        self.assertEqual(post_group_0, PostsPagesTest.group.title)
        self.assertEqual(post_group_1, PostsPagesTest.group.title)

    def test_profile_page_show_correct_context(self):
        """Проверка контекста страницы профиля"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTest.post.author}
            )
        )
        post_0 = response.context['page_obj'][0]
        post_1 = response.context['page_obj'][1]
        post_author_0 = post_0.author
        post_author_1 = post_1.author
        self.assertEqual(post_author_0, PostsPagesTest.user)
        self.assertEqual(post_author_1, PostsPagesTest.user)

    def test_post_detail_page_show_correct_context(self):
        """Проверка контекста страницы поста"""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTest.post.pk}
            )
        )
        post = response.context['one_post']
        post_pk = post.pk
        self.assertEqual(post_pk, PostsPagesTest.post.pk)

    def test_post_create_page_show_correct_context(self):
        """Проверка контекста страницы создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Проверка контекста страницы редактирования поста"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTest.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        post_id = response.context['post_id']
        self.assertEqual(post_id, PostsPagesTest.post.pk)

    def test_post_image_form(self):
        """Проверка создания поста с изображением"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='image.gif',
            content=PostsPagesTest.image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост с картинкой',
            'group': PostsPagesTest.group.pk,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/image.gif'
            ).exists()
        )

    def test_post_image_context(self):
        """Проверка передачи изображения в контекст"""
        response_home = self.guest_client.get(
            reverse('posts:index')
        )
        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTest.post_img.author}
            )
        )
        response_group = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTest.post_img.group.slug}
            )
        )
        response_detail = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTest.post_img.pk}
            )
        )
        last_post = Post.objects.latest('pub_date')
        context_home = response_home.context['page_obj'][0].image.name
        context_profile = response_profile.context['page_obj'][0].image.name
        context_group = response_group.context['page_obj'][0].image.name
        context_detail = response_detail.context['one_post'].image.name
        self.assertEqual(last_post.image.name, context_home)
        self.assertEqual(last_post.image.name, context_profile)
        self.assertEqual(last_post.image.name, context_group)
        self.assertEqual(last_post.image.name, context_detail)

    def test_comment_post_login_user(self):
        """Проверка комментариев для авторизированного клиента"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'коммент'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsPagesTest.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text']
            ).exists()
        )

    def test_comment_post_guest_user(self):
        """Проверка комментариев для гостевого клиента"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'коммент'
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsPagesTest.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text']
            ).exists()
        )

    def test_comment_show_page(self):
        """Проверка передачи комментариев в контекст"""
        form_data = {
            'text': 'коммент'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsPagesTest.post.pk}
            ),
            data=form_data,
            follow=True
        )
        response_2 = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTest.post.pk}
            )
        )
        context = response_2.context['comments']
        last_comment = Comment.objects.get(
            text=form_data['text']
        )
        self.assertIn(last_comment, context)

    def test_cache_index(self):
        """Проверка кеша главной страницы"""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        content = response.content
        Post.objects.create(
            text='тестовый пост кеш',
            author=PostsPagesTest.user
        )
        response_cache = self.authorized_client.get(
            reverse('posts:index')
        )
        content_cache = response_cache.content
        self.assertEqual(content, content_cache)
        cache.clear()
        response_new = self.authorized_client.get(
            reverse('posts:index')
        )
        content_new = response_new.content
        self.assertNotEqual(content_cache, content_new)


class PaginatorViewsTest(TestCase):
    """Тесты пажинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Поклонники',
            slug='Fan',
            description='Тестовое описание'
        )
        cls.test_posts_set = [Post(
            text=f'Тестовый пост {num}',
            author=cls.user,
            group=cls.group
        ) for num in range(15)]
        Post.objects.bulk_create(cls.test_posts_set)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_main_page_correct_paginate_posts(self):
        """Проверка пажинатора на главной странице"""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        response_page_2 = self.guest_client.get(
            reverse('posts:index')
            + '?page=2'
        )
        pages_post = {
            len(response.context['page_obj']): 10,
            len(response_page_2.context['page_obj']): 5
        }
        for response, length in pages_post.items():
            with self.subTest(response=response):
                self.assertEqual(response, length)

    def test_group_list_page_paginate_posts_with_correct_group(self):
        """Проверка пажинатора на страницах группы"""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            )
        )
        response_page_2 = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ) + '?page=2'
        )
        post_group_test = response.context['page_obj'][0]
        post_group_test_2 = response_page_2.context['page_obj'][0]
        pages_post = {
            len(response.context['page_obj']): 10,
            len(response_page_2.context['page_obj']): 5
        }
        post_equal_group = {
            post_group_test.group: PaginatorViewsTest.group,
            post_group_test_2.group: PaginatorViewsTest.group
        }
        for response, length in pages_post.items():
            with self.subTest(response=response):
                self.assertEqual(response, length)
        for post_group, group in post_equal_group.items():
            with self.subTest(post_group=post_group):
                self.assertEqual(post_group, group)

    def test_profile_page_paginate_posts_with_correct_author(self):
        """Проверка пажинатора на страницах профиля"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user}
            )
        )
        response_page_2 = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user}
            ) + '?page=2'
        )
        post_author_0 = response.context['page_obj'][0]
        post_author_1 = response_page_2.context['page_obj'][0]
        pages_post = {
            len(response.context['page_obj']): 10,
            len(response_page_2.context['page_obj']): 5
        }
        post_equal_author = {
            post_author_0.author: PaginatorViewsTest.user,
            post_author_1.author: PaginatorViewsTest.user
        }
        for response, length in pages_post.items():
            with self.subTest(response=response):
                self.assertEqual(response, length)
        for post_author, user in post_equal_author.items():
            with self.subTest(post_author=post_author):
                self.assertEqual(post_author, user)


class TestPostCreate(TestCase):
    """Тесты отображения созданного поста на страницах"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Поклонники',
            slug='Fan',
            description='Тестовое описание'
        )
        cls.group_2 = Group.objects.create(
            title='Увлечение',
            slug='hobbies',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='текстовый пост',
            group=cls.group
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Текстовый пост 2',
            group=cls.group
        )
        cls.post_3 = Post.objects.create(
            author=cls.user,
            text='Текстовый пост 3',
            group=cls.group_2
        )

    def setUp(self):
        self.auhtorized_client = Client()
        self.auhtorized_client.force_login(self.user)

    def test_post_with_group_located_in_correct_pages(self):
        """Проверка корректного отображения созданных постов"""
        response_home_page = self.auhtorized_client.get(reverse('posts:index'))
        response_group_list_page = self.auhtorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': TestPostCreate.group.slug}
            )
        )
        response_profile_page = self.auhtorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': TestPostCreate.user}
            )
        )
        response_group_list_page_2 = self.auhtorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': TestPostCreate.group_2.slug}
            )
        )
        home_page = response_home_page.context['page_obj']
        group_page = response_group_list_page.context['page_obj']
        profile_page = response_profile_page.context['page_obj']
        group_page_2 = response_group_list_page_2.context['page_obj']
        self.assertIn(TestPostCreate.post, home_page)
        self.assertIn(TestPostCreate.post, group_page)
        self.assertIn(TestPostCreate.post, profile_page)
        self.assertNotIn(TestPostCreate.post, group_page_2)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.user_2 = User.objects.create(username='TestUser2')
        cls.user_3 = User.objects.create(username='TestUser3')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TestFollow.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(TestFollow.user_3)

    def test_follow_auth_user(self):
        """Проверка подписки и отписки на автора"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user_2}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=TestFollow.user,
                author=TestFollow.user_2
            ).exists()
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TestFollow.user_2}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=TestFollow.user,
                author=TestFollow.user_2
            ).exists()
        )

    def test_post_follow_page(self):
        """Пост пользователя появляется в ленте"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user_2}
            )
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=TestFollow.user_2
        )
        response_follow_post = self.authorized_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        context = response_follow_post.context['page_obj']
        self.assertIn(post, context)
        response_unfollow = self.authorized_client_2.get(
            reverse(
                'posts:follow_index'
            )
        )
        context_unfollow = response_unfollow.context['page_obj']
        self.assertNotIn(post, context_unfollow)

    def test_follow_yourself(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=TestFollow.user,
                author=TestFollow.user
            ).exists()
        )

    def test_follow_once(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user_2}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=TestFollow.user,
                author=TestFollow.user_2
            ).exists()
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollow.user_2}
            )
        )
        follow_count = Follow.objects.filter(
            user=TestFollow.user,
            author=TestFollow.user_2
        ).count()
        self.assertEqual(follow_count, 1)
