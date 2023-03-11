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
            slug='Тест',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки сокращений',
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        text = post.text
        group = PostModelTest.group
        title = group.title
        self.assertEqual(str(post), text[:15])
        self.assertEqual(str(group), title)
