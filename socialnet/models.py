from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime, timedelta
from uuid import uuid4
import jwt


class User(AbstractUser):

    id = models.UUIDField(primary_key=True, default=uuid4, null=False)
    first_name = models.CharField(verbose_name='Имя', max_length=40)
    last_name = models.CharField(verbose_name='Фамилия', max_length=40)
    username = models.CharField(blank=True, verbose_name='Никнейм', max_length=10, unique=True)
    email = models.EmailField(verbose_name='Email', unique=True, max_length=128)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        exp_time = datetime.now() + timedelta(hours=1)
        token = jwt.encode(payload={'username': self.username, 'exp': int(exp_time.strftime("%s"))},
                           key=settings.SECRET_KEY,
                           algorithm='HS256')
        return token.decode('utf-8')


class Article(models.Model):
    slug = models.SlugField(max_length=50, verbose_name='Заголовок (транслитом)', db_index=True, null=False, unique=True)
    header = models.CharField(max_length=50, verbose_name='Заголовок', null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    summary = models.CharField(max_length=250, verbose_name='Краткое содержание', null=False)
    description = models.CharField(verbose_name='Содержание', max_length=750, null=False)
    reviews = models.IntegerField(verbose_name='Просмотры', default=0)
    rating = models.FloatField(verbose_name='Рейтинг', default=0)
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')

    def __str__(self):
        return f'{self.header}'


class Rating(models.Model):

    class RatingChoices(models.IntegerChoices):
        __empty__ = 'Оцените статью'
        LOW = -1, 'Не понравилась'
        NORMAL = 0, 'Нормально'
        EXCELLENT = 1, 'Отлично'

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_fk')
    mark = models.IntegerField(verbose_name='Рейтинг', default=RatingChoices.NORMAL, choices=RatingChoices.choices)




