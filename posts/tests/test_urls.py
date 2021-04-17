from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='test group',
            slug='test-slug',
            description='For testing',
        )
        Post.objects.create(
            text='test post',
            author=User.objects.create_user(username='test_user'),
            group=Group.objects.get(title='test group')
        )
        cls.url_index = reverse('index')
        cls.url_group = reverse(
            'group',
            kwargs={'slug': 'test-slug'}
        )
        cls.url_profile = reverse(
            'profile',
            kwargs={'username': 'test_user'}
        )
        cls.url_post = reverse(
            'post',
            kwargs={'username': 'test_user', 'post_id': 1}
        )
        cls.url_new_post = reverse('new_post')
        cls.url_post_edit = reverse(
            'post_edit',
            kwargs={'username': 'test_user', 'post_id': 1}
        )
        cls.url_follow_index = reverse('follow_index')
        cls.url_profile_follow = reverse(
            'profile_follow',
            kwargs={'username': 'test_user'}
        )
        cls.url_profile_unfollow = reverse(
            'profile_unfollow',
            kwargs={'username': 'test_user'}
        )
        cls.url_add_comment = reverse(
            'add_comment',
            kwargs={'username': 'test_user', 'post_id': 1}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_no_author = User.objects.create_user(
            username='test_no_author')
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)

    def test_group_slug_profile_post(self):
        """Доступность страницы групп/слаг, профайл пользователя
        и страницы поста для всех"""
        urls_name = {
            self.url_group,
            self.url_profile,
            self.url_post,
        }
        for url_name in urls_name:
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertEqual(response.status_code, 200)

    def test_new_post_for_authorized_client(self):
        """Доступность страниц для авторизированного
        пользователя/автора поста: creat and edit post, follow_index"""
        urls_name = {
            self.url_new_post,
            self.url_post,
            self.url_follow_index,
        }
        for url_name in urls_name:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(url_name)
                self.assertEqual(response.status_code, 200)

    def test_redirect_for_guest_client(self):
        """Редирект создания и редактирования поста для гостя
        Редирект страницы с подпиской для гостя
        редирект при комментировании поста"""
        urls_redirect_name = {
            self.url_new_post:
                f'{reverse("login")}?next={self.url_new_post}',
            self.url_post_edit:
                f'{reverse("login")}?next={self.url_post_edit}',
            self.url_follow_index:
                f'{reverse("login")}?next={self.url_follow_index}',
            self.url_profile_follow:
                f'{reverse("login")}?next={self.url_profile_follow}',
            self.url_profile_unfollow:
                f'{reverse("login")}?next={self.url_profile_unfollow}',
            self.url_add_comment:
                f'{reverse("login")}?next={self.url_add_comment}',
        }
        for urls_name, redirect_name in urls_redirect_name.items():
            with self.subTest(urls_name=urls_name):
                response = self.guest_client.get(urls_name, follow=True)
                self.assertRedirects(response, redirect_name)

    def test_redirect_edit_post_no_author(self):
        """Редирект редактирования поста не его автором"""
        response = self.authorized_client_no_author.get(
            self.url_post_edit,
            follow=True)
        self.assertRedirects(
            response,
            self.url_post)

    def test_urls_uses_correct_templates(self):
        """Использование правильных шаблонов"""
        templates_urls_name = {
            self.url_index: 'index.html',
            self.url_group: 'group.html',
            self.url_new_post: 'post_new.html',
            self.url_post_edit: 'post_new.html',
            self.url_profile: 'profile.html',
            self.url_post: 'post.html',
            self.url_follow_index: 'follow.html',
        }
        for reverse_name, template in templates_urls_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_return_404_if_no_page(self):
        response = self.guest_client.get(reverse(
            'profile', kwargs={'username': 'no_test_user'}))
        self.assertEqual(response.status_code, 404)
