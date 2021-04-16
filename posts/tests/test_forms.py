import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(title='test_group', slug='test_slug')
        Post.objects.create(
            text='testing text',
            author=cls.user,
            group=cls.group,
        )
        cls.post = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверяем создание нового поста"""
        post_count = Post.objects.count()
        test_group = self.group.id
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
        post_data = {
            'group': test_group,
            'text': 'testing text',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=post_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=test_group,
                text='testing text',
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Проверяем редактирование поста"""
        post_count = Post.objects.count()
        test_group = self.group.id
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_new.gif',
            content=small_gif,
            content_type='image_new/gif'
        )
        post_data_edit = {
            'group': test_group,
            'text': 'testing text edit',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': 'test_user', 'post_id': 1}),
            data=post_data_edit,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': 'test_user', 'post_id': 1}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                group=test_group,
                text='testing text edit',
                image='posts/small_new.gif',
            ).exists()
        )
