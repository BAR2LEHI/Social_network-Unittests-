from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden


User = get_user_model()


class TestCoreViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='TestUser'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_template_404(self):
        response = self.authorized_client.get('/unexisting-page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_template_403(self):
        response = self.guest_client.post(f'profile/{TestCoreViews.user}/unfollow/')
        self.assertEqual('core/403_csrf.html', 'core/403_csrf.html')
