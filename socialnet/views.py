from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.db.models import F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormView, FormMixin
from .forms import RegisterForm, LoginForm, ArticleForm, SettingForm, OrderAndFilterForm, FavouriteForm, RateForm
from .models import Article, User


class RegisterView(CreateView):
    """
    Обработка регистрации юзера
    """
    form_class = RegisterForm
    template_name = 'signup.html'
    success_url = 'index'

    def form_valid(self, form):
        """
        После отправки (валидации) формы логиним юзера
        :param form:
        :return:
        """
        user = form.save()
        login(self.request, user)
        return super(RegisterView, self).form_valid(form)


class UserLoginView(LoginView):
    """
    Обработка входа юзера
    """
    template_name = 'login.html'
    authentication_form = LoginForm
    success_url = 'index'

    def form_valid(self, form):
        """
        После отправки (валидации) формы ищём юзера в БД и затем логиним его
        :param form:
        :return: HttpResponseRedirect
        """
        cd = form.cleaned_data
        user = authenticate(self.request, email=cd['username'], password=cd['password'])
        login(self.request, user)
        return super(UserLoginView, self).form_valid(form)


class UserLogoutView(LogoutView):
    """
    Обработка выхода юзера редиректом на страницу входа
    """
    next_page = 'login'


class ArticleView(ListView):
    """
    Обработка показа статей
    """
    model = Article
    template_name = 'index.html'
    context_object_name = 'articles'
    # Добавляем в контекст форму для фильтрации и сортировки
    extra_context = {'form': OrderAndFilterForm()}

    def get_queryset(self):
        """
        Обработка выдачи статей
        Если в GET-запросе переданы с формы данные для фильрации/сортировки, тогда фильтруем/сортируем
        Иначе, возвращаем все записи из БД
        :return: QuerySet
        """
        queryset = Article.objects.all()
        if {'date_order', 'rating_order', 'filter_by_slug'} != self.request.GET.keys():
            return queryset
        else:
            filter_by = self.request.GET.get('filter_by_slug')
            order_by_date = self.request.GET.get('date_order')
            order_by_rating = self.request.GET.get('rating_order')
            queryset = Article.objects.filter(Q(slug__icontains=filter_by)).order_by(order_by_date, order_by_rating)
            return queryset

    def get_paginate_by(self, queryset):
        """
        Получаем от cookies кол-во записей на одной странице,
        если ещё не установлены, то возвращаем значение по умолчанию - 10
        :param queryset:
        :return: int - кол-во записей на одной странице
        """
        return self.request.COOKIES.get('paginate_by', 10)


class DetailArticle(FormMixin, ArticleView):
    """
    Обработка просмотра детальной информации по статье
    Добавлем форму для оценки, наследуясь от FormMixin
    """
    form_class = FavouriteForm
    extra_context = {'rate_form': RateForm(),
                     'button_rate': 'Оценить'}

    def get_queryset(self):
        """
        Инкрементим кол-во просмотров к текущей статье
        :return: QuerySet
        """
        article = Article.objects.filter(slug=self.kwargs['slug'])
        article.update(reviews=F("reviews") + 1)
        return article

    def get(self, request, *args, **kwargs):
        """
        Обработка фиксации понравившихся статей
        Понравившиеся статьи ложим в cookies с сохранением их slug поля
        Далее редиректим на главную страницу - 'index'
        :param request:
        :param args:
        :param kwargs:
        :return: HttpResponseRedirect
        """
        if 'like' not in request.GET:
            return super(DetailArticle, self).get(request, *args, **kwargs)
        else:
            like = request.GET.get('like', 'off')
            response = HttpResponseRedirect(reverse('index'), 'Ваша оценка успешно отправлена!')
            cookies = request.COOKIES.get('likes', '')
            current_article_slug = self.get_queryset().values('slug')[0]['slug']
            if like == 'on':
                response.set_cookie(key='likes', value=cookies + current_article_slug + ',', secure=True, samesite='strict')
            elif like == 'off':
                updated_cookies = cookies.replace(current_article_slug + ',', '')
                response.set_cookie(key='likes', value=updated_cookies, secure=True, samesite='strict')
            return response

    def get_initial(self):
        """
        Устанавливаем checkbox выделенным,
        чтобы юзер знал, что он уже оценивал текущую статью
        :return: dict - данные формы
        """
        initial = super(DetailArticle, self).get_initial()
        current_article_slug = self.get_queryset().values('slug')[0]['slug']
        cookies = self.request.COOKIES.get('likes', '')
        initial['like'] = True if current_article_slug in cookies else False
        return initial


class FavouriteView(LoginRequiredMixin, ArticleView):
    """
    Обработка получения понравившихся статей
    """
    login_url = 'login'

    def get_queryset(self):
        """
        Получаем понравившиеся статьи путём фильрации объектов модели по slug
        извлечёнными из cookies
        :return: QuerySet
        """
        favourites = self.request.COOKIES.get('likes', '').split(',')[:-1]
        articles = Article.objects.filter(slug__in=favourites)
        return articles


class CreateArticleView(LoginRequiredMixin, CreateView):
    """
    Обработка создния статьи
    """
    model = Article
    form_class = ArticleForm
    template_name = 'add.html'
    login_url = 'login'
    success_url = '/detail/{slug}'

    def form_valid(self, form):
        """
        После успешной отправки (валидации) формы сохраняем данные статьи в БД
        :param form:
        :return:
        """
        data = form.cleaned_data
        article = Article(author_id=self.request.user.id, **data)
        article.save()
        return super(CreateArticleView, self).form_valid(form)


class SettingsView(FormView):
    """
    Обработка изменения кол-ва статей на одной странице
    """
    form_class = SettingForm
    template_name = 'setting.html'

    def get_initial(self):
        """
        Устанавливаем в input число ,
        чтобы юзер знал последнее сохранённое кол-во статей на одной странице
        :return: dict - данные формы
        """
        initial = super(SettingsView, self).get_initial()
        initial['paginate_by'] = self.request.COOKIES.get('paginate_by', 10)
        return initial

    def form_valid(self, form):
        """
        После успешной отправки (валидации) формы сохраняем данные в cookies
        редиректим на главную страницу - 'index'
        :param form:
        :return: HttpResponseRedirect
        """
        cd = form.cleaned_data
        response = HttpResponseRedirect(reverse('index'), 'Настройки успешно сохранены!')
        response.set_cookie(key='paginate_by', value=cd['paginate_by'], secure=True, samesite='strict')
        return response
