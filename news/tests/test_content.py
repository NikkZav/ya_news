from django.test import TestCase
from news.models import News, Comment
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from news.forms import CommentForm

from datetime import datetime, timedelta


User = get_user_model()

class TestHomePage(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        today = datetime.today()
        News.objects.bulk_create(
            News(
                title=f'{i}',
                text='text',
                date=today - timedelta(days=i)
            )
            for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        )

    def test_news_count(self):
        resopnse = self.client.get(self.HOME_URL)
        object_list = resopnse.context['object_list']
        news_count = object_list.count()
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_dates = [news.date for news in object_list]
        # Сортируем полученный список по убыванию.
        sorted_dates = sorted(all_dates, reverse=True)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)

class TestComment(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='title', text='text')
        cls.author = User.objects.create(username='Commentator')
        now = timezone.now()

        for i in range(10):
            comment = Comment.objects.create(
                news=cls.news,
                author=cls.author,
                text=f'{i}'
            )
            comment.created = now + timedelta(days=i)
            comment.save()

        cls.detail_url = reverse('news:detail', args=(cls.news.id,))

    def test_comments_order(self):
        response = self.client.get(self.detail_url)
        self.assertIn('news', response.context)
        news = response.context['news']
        all_comments = news.comment_set.all()
        all_timestamps = [comment.created for comment in all_comments]
        sorted_timestamps = sorted(all_timestamps)
        self.assertEqual(all_timestamps, sorted_timestamps)

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIsInstance(form, CommentForm)
