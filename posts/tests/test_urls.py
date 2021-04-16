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
            reverse('group', kwargs={'slug': 'test-slug'}),
            reverse('profile', kwargs={'username': 'test_user'}),
            reverse('post', kwargs={'username': 'test_user', 'post_id': 1}),
        }
        for url_name in urls_name:
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertEqual(response.status_code, 200)

    def test_new_post_for_authorized_client(self):
        """Доступность страниц для авторизированного
        пользователя/автора поста: creat and edit post, follow_index"""
        urls_name = {
            reverse('new_post'),
            reverse('post_edit', kwargs={
                'username': 'test_user', 'post_id': 1}),
            reverse('follow_index'),
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
            reverse('new_post'): '/auth/login/?next=/new/',
            reverse('post_edit', kwargs={
                'username': 'test_user',
                'post_id': 1}): '/auth/login/?next=/test_user/1/edit/',
            reverse('follow_index'): '/auth/login/?next=/follow/',
            reverse('profile_follow', kwargs={
                'username': 'test_user'}
            ): '/auth/login/?next=/test_user/follow/',
            reverse('profile_unfollow', kwargs={
                'username': 'test_user'}
            ): '/auth/login/?next=/test_user/unfollow/',
            reverse('add_comment', kwargs={
                'username': 'test_user',
                'post_id': 1}
            ): '/auth/login/?next=/test_user/1/comment/',
        }
        for urls_name, redirect_name in urls_redirect_name.items():
            with self.subTest(urls_name=urls_name):
                response = self.guest_client.get(urls_name, follow=True)
                self.assertRedirects(response, redirect_name)

    def test_redirect_edit_post_no_author(self):
        """Редирект редактирования поста не его автором"""
        response = self.authorized_client_no_author.get(
            reverse('post_edit', kwargs={
                'username': 'test_user', 'post_id': 1}),
            follow=True)
        self.assertRedirects(response, '/test_user/1/')

    def test_urls_uses_correct_templates(self):
        """Использование правильных шаблонов"""
        templates_urls_name = {
            '/': 'index.html',
            '/group/test-slug/': 'group.html',
            '/new/': 'post_new.html',
            '/test_user/1/edit/': 'post_new.html',
            '/test_user/': 'profile.html',
            '/test_user/1/': 'post.html',
            '/follow/': 'follow.html',
        }
        for reverse_name, template in templates_urls_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_return_404_if_no_page(self):
        response = self.guest_client.get(reverse(
            'profile', kwargs={'username': 'no_test_user'}))
        self.assertEqual(response.status_code, 404)
