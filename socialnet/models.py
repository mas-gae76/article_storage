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
    id = models.IntegerField(primary_key=True, null=False)
    slug = models.SlugField(max_length=50, verbose_name='Заголовок (транслитом)', db_index=True, null=False)
    header = models.CharField(max_length=50, verbose_name='Заголовок', null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    summary = models.CharField(max_length=250, verbose_name='Краткое содержание', null=False)
    description = models.CharField(verbose_name='Содержание', max_length=750, null=False)
    reviews = models.IntegerField(verbose_name='Просмотры')
    rating = models.IntegerField(verbose_name='Рейтинг')

    def __str__(self):
        return self.header


class Rating(models.Model):

    class RatingChoices(models.IntegerChoices):
        __empty__ = 'Оцените статью'
        LOW = -1, 'Не понравилась'
        NORMAL = 0, 'Нормально'
        EXCELLENT = 1, 'Отлично'

    who = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Кто оценил?')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_fk', default=None)
    mark = models.IntegerField(verbose_name='Рейтинг', default=RatingChoices.NORMAL, choices=RatingChoices.choices)


class Favourites(models.Model):
    who = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='У кого?')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, default='')
    is_favourite = models.BooleanField(default=False, verbose_name='В избранном?')




