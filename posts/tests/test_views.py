import datetime
import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Follow, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.another_user = User.objects.create_user(
            username='test_another_user'
        )
        cls.follower = User.objects.create_user(username='follower')
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
        uploaded_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        uploaded_follower = SimpleUploadedFile(
            name='small_follower.gif',
            content=small_gif,
            content_type='image/gif'
        )
        Group.objects.create(
            title='Test',
            slug='test-slug',
            description='For testing',
        )
        Post.objects.create(
            text='test_post',
            author=cls.author,
            group=Group.objects.create(
                title='test_group',
                slug='test_group',
            ),
            image=uploaded,
        )
        Post.objects.create(
            text='test_follower_post',
            author=cls.follower,
            group=Group.objects.create(
                title='test_follower_group',
                slug='test_follower_group',
            ),
            image=uploaded_follower,
        )
        Post.objects.create(
            text='test_another_post',
            author=cls.another_user,
            group=Group.objects.create(
                title='test_another_group',
                slug='test_another_group',
            ),
            image=uploaded_2,
        )
        Follow.objects.create(
            user=cls.author,
            author=cls.follower,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = self.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def get_first_context_for_authorized_client(self, request, field):
        response = self.authorized_client.get(request)
        first_object = response.context[field][0]
        return first_object

    def test_pages_used_correced_template(self):
        """Страницы используют нужные шаблоны"""
        template_pages_names = {
            reverse('index'): 'index.html',
            reverse('follow_index'): 'follow.html',
            reverse('group', kwargs={'slug': 'test-slug'}): 'group.html',
            reverse('new_post'): 'post_new.html',
            reverse('profile', kwargs={'username': 'test_user'}):
                'profile.html',
            reverse('post', kwargs={'username': 'test_user', 'post_id': 1}):
                'post.html',
            reverse('post_edit', kwargs={
                'username': 'test_user', 'post_id': 1}):
                'post_new.html',
        }
        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_mail_pages_have_correct_count_posts(self):
        """Index и Follow имеет правильно количество постов"""
        count_posts = {
            reverse('index'): 3,
            reverse('follow_index'): 1,
        }
        for url, count in count_posts.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page']), count)

    def test_index_page_shows_correct_context(self):
        """Index правильно заполняется данными"""
        first_object = self.get_first_context_for_authorized_client(
            reverse('index'),
            'page'
        )
        post_data_all = {
            first_object.text: 'test_another_post',
            first_object.pub_date.date(): datetime.datetime.now().date(),
            first_object.author.username: 'test_another_user',
            first_object.group.title: 'test_another_group',
            first_object.image: 'posts/small_2.gif',
        }
        for post_data, expect in post_data_all.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expect)

    def test_follow_index_page_show_correct_context(self):
        """Follow_Index правильно заполняется данными"""
        first_object = self.get_first_context_for_authorized_client(
            reverse('follow_index'),
            'page'
        )
        post_data_all = {
            first_object.text: 'test_follower_post',
            first_object.pub_date.date(): datetime.datetime.now().date(),
            first_object.author.username: 'follower',
            first_object.group.title: 'test_follower_group',
            first_object.image: 'posts/small_follower.gif',
        }
        for post_data, expect in post_data_all.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expect)

    def test_follow_page_dont_show_unfollowing(self):
        """Follow не показывает пост не подписанного автора"""
        first_object = self.get_first_context_for_authorized_client(
            reverse('follow_index'),
            'page'
        )
        self.assertNotEqual(first_object.text,
                            'test_another_post')
        self.assertNotEqual(first_object.author.username,
                            'test_another_user')
        self.assertNotEqual(first_object.group.title,
                            'test_another_group')

    def test_group_pages_show_correct_context(self):
        """Пост попадает в нужную группу"""
        date_today = datetime.datetime.now().date()
        first_object = self.get_first_context_for_authorized_client(
            reverse('group', kwargs={'slug': 'test_group'}),
            'page'
        )
        post_data_all = {
            first_object.text: 'test_post',
            first_object.pub_date.date(): date_today,
            first_object.author.username: 'test_user',
            first_object.group.title: 'test_group',
            first_object.image: 'posts/small.gif',
        }
        for post_data, expect in post_data_all.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expect)

    def test_another_group_pages_dont_show_context(self):
        """Пост не попадает в другую группу"""
        first_object = self.get_first_context_for_authorized_client(
            reverse('group', kwargs={'slug': 'test_another_group'}),
            'page'
        )
        self.assertNotEqual(first_object.text, 'test_post')
        self.assertNotEqual(first_object.group.title,
                            'test_group')

    def test_post_pages_show_correct_context(self):
        """Данные поста отображаются на странице поста"""
        date_today = datetime.datetime.now().date()
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'test_user', 'post_id': 1}))
        post_object = response.context['post']
        post_data_all = {
            post_object.text: 'test_post',
            post_object.pub_date.date(): date_today,
            post_object.author.username: 'test_user',
            post_object.group.title: 'test_group',
            post_object.image: 'posts/small.gif',
        }
        for post_data, expect in post_data_all.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expect)

    def test_user_pages_show_correct_context(self):
        """Пост попадает на страницу пользователя"""
        date_today = datetime.datetime.now().date()
        first_object = self.get_first_context_for_authorized_client(
            reverse('profile', kwargs={'username': 'test_user'}),
            'page'
        )
        post_data_all = {
            first_object.text: 'test_post',
            first_object.pub_date.date(): date_today,
            first_object.author.username: 'test_user',
            first_object.group.title: 'test_group',
            first_object.image: 'posts/small.gif',
        }
        for post_data, expect in post_data_all.items():
            with self.subTest(post_data=post_data):
                self.assertEqual(post_data, expect)

    def test_another_user_pages_dont_show_context(self):
        """Пост не попадает на страницу другого пользователя"""
        first_object = self.get_first_context_for_authorized_client(
            reverse('profile', kwargs={'username': 'test_another_user'}),
            'page'
        )
        self.assertNotEqual(first_object.text, 'test_post')
        self.assertNotEqual(first_object.group.title,
                            'test_group')

    def test_new_post_shows_correct_form(self):
        """Шаблон new post имеет корректные поля"""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_shows_correct_form(self):
        """Шаблон new post имеет корректные поля"""
        response = self.authorized_client.get(reverse(
            'post_edit', kwargs={'username': 'test_user', 'post_id': 1}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_cant_load_no_picture(self):
        text = ('Try load text file instead picture').encode()
        uploaded = SimpleUploadedFile(
            name='text.txt',
            content=text,
            content_type='text/plain'
        )
        post_data = {
            'group': Group.objects.get(title='test_group'),
            'text': 'testing text',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=post_data,
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'image',
            'Загрузите правильное изображение. '
            'Файл, который вы загрузили, '
            'поврежден или не является изображением.',
        )

    def test_add_follower(self):
        author = self.another_user
        count_befor_follow = author.following.count()
        self.authorized_client.get(
            reverse('profile_follow', kwargs={
                'username': author.username})
        )
        count_after_follow = author.following.count()
        self.assertEqual(count_befor_follow + 1, count_after_follow)

    def test_unfollowing(self):
        author = self.follower
        count_befor_unfollow = author.following.count()
        self.authorized_client.get(
            reverse('profile_unfollow', kwargs={
                'username': author.username})
        )
        count_after_unfollow = author.following.count()
        self.assertEqual(count_befor_unfollow - 1, count_after_unfollow)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_user = User.objects.create_user(username='test_user')
        test_group = Group.objects.create(title='test_group', slug='test')
        for test_post_number in range(13):
            text_post = 'test_post_' + str(test_post_number)
            Post.objects.create(
                text=text_post,
                author=test_user,
                group=test_group
            )

    def test_first_page_contains_ten_records(self):
        """Проверка, что на первой странице правильное количество постов"""
        page_names = {
            reverse('index'): 'page',
            reverse('group', kwargs={'slug': 'test'}): 'page',
            reverse('profile', kwargs={'username': 'test_user'}): 'page',
        }
        for reverse_name, context_name in page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get(context_name).object_list), 10)

    def test_second_page_contains_three_records(self):
        """Проверка, что на второй странице правильное количство постов"""
        page_names = {
            reverse('index'): 'page',
            reverse('group', kwargs={'slug': 'test'}): 'page',
            reverse('profile', kwargs={'username': 'test_user'}): 'page',
        }
        for reverse_name, context_name in page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(
                    response.context.get(context_name).object_list), 3)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
        )
        Post.objects.create(
            text='test_post',
            author=cls.user,
            group=cls.group,
        )

    def test_cache_index_page(self):
        response_before = self.client.get(reverse('index'))
        content_before = response_before.content
        Post.objects.create(
            text='test_post_second',
            author=self.user,
            group=self.group,
        )
        response_after = self.client.get(reverse('index'))
        content_after = response_after.content
        cache.clear()
        response_after_clear = self.client.get(reverse('index'))
        content_after_clear = response_after_clear.content
        self.assertEqual(content_before, content_after)
        self.assertNotEqual(content_before, content_after_clear)
