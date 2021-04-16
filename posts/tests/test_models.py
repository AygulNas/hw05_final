from django.test import TestCase

from posts.models import Comment, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст ' * 3,
            pub_date='1.4.2021',
            author=User.objects.create_user(username='Тестовый пользователь'),
            group=Group.objects.create(title='Тестовая группа')
        )

    def test_title_label(self):
        post = PostModelTest.post
        verbose_names_all = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }
        for label, expected in verbose_names_all.items():
            with self.subTest(label=label):
                verbose = post._meta.get_field(label).verbose_name
                self.assertEquals(verbose, expected)

    def test_title_help_text(self):
        post = PostModelTest.post
        help_text_all = {
            'text': 'Добавьте ваш текст сюда',
            'image': 'Загрузите картинку',
        }
        for label, expected in help_text_all.items():
            with self.subTest(label=label):
                help_text = post._meta.get_field(label).help_text
                self.assertEquals(help_text, expected)

    def test_str(self):
        post = PostModelTest.post
        self.assertEqual(post.__str__(), post.text[:15])


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестирование',
            slug='т' * 50,
            description='Тестовое содержание',
        )

    def test_verbose_name(self):
        group = GroupModelTest.group
        field_verbose = {
            'title': 'Название группы',
            'description': 'Описание группы'
        }
        for value, expected in field_verbose.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        group = GroupModelTest.group
        field_help_text = {
            'title': 'Введите название группы',
            'slug': 'Укажите адрес для страницы задачи. Используйте только '
                    'латиницу, цифры, дефисы и знаки подчёркивания',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected
                )

    def test_str(self):
        group = GroupModelTest.group
        self.assertEquals(group.__str__(), group.title)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        author_test = User.objects.create_user(username='test_user')
        cls.comment = Comment.objects.create(
            post=Post.objects.create(text='test_post', author=author_test),
            author=author_test,
            text='test_text',
            created='1.4.2021',
        )

    def test_verbose_name(self):
        """Проверка наименований полей в Comments"""
        comment = CommentModelTest.comment
        verbose = comment._meta.get_field('text').verbose_name
        self.assertEquals(verbose, 'Комментарий')

    def test_help_text(self):
        comment = CommentModelTest.comment
        help_text = comment._meta.get_field('text').help_text
        self.assertEquals(help_text, 'Напишите ваш комментарий'
                                     'в соотвествии с правилами сообщества')
