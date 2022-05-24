from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.db.models import F, Q
from django.http import HttpResponseRedirect
from django.shortcuts import reverse, redirect
from django.views.generic import CreateView, ListView
from django.views.generic.edit import FormView, FormMixin
from .forms import RegisterForm, LoginForm, ArticleForm, SettingForm, OrderAndFilterForm, FavouriteForm, RateForm
from .models import Article, Favourites


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
        return redirect('index')


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
            queryset = Article.objects.filter(Q(slug__icontains=filter_by)).order_by(order_by_rating,order_by_date)
            return queryset

    def get_paginate_by(self, queryset) -> int:
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
    checked = False

    def get_queryset(self):
        """
        Инкрементим кол-во просмотров к текущей статье
        :return: QuerySet
        """
        article = Article.objects.filter(slug=self.kwargs['slug'])
        DetailArticle.queryset = article
        article.update(reviews=F("reviews") + 1)
        return article

    def get(self, request, *args, **kwargs):
        """
        Обработка фиксации понравившихся статей
        Понравившиеся статьи ложим в cookies с сохранением их id
        Далее редиректим на главную страницу - 'index'
        :param request:
        :param args:
        :param kwargs:
        :return: HttpResponseRedirect
        """
        
        if 'like' not in request.GET and not DetailArticle.checked:
            return super(DetailArticle, self).get(request, *args, **kwargs)
        else:
            like = request.GET.get('like', '')
            cookies = request.COOKIES.get('likes', '')
            current_article = str(DetailArticle.queryset.values('id')[0]['id'])
            response = HttpResponseRedirect(reverse('favourites'), 'Ваша оценка успешно отправлена!')
            if like == 'on':
                response.set_cookie(key='likes', value=cookies + current_article + ',',
                                    secure=True, samesite='strict')
            elif DetailArticle.checked:
                """
                Если залогиненный юзер хочет убрать из избранного статью, то ищем в БД эту статью и удаляем её
                """
                DetailArticle.checked = False
                updated_cookies = cookies.replace(current_article + ',', '')
                response.set_cookie(key='likes', value=updated_cookies, secure=True, samesite='strict')
                if self.request.user.is_authenticated:
                    Favourites.objects.filter(who=self.request.user, article_id=current_article).delete()
            return response

    def get_initial(self):
        """
        Устанавливаем checkbox выделенным,
        чтобы юзер знал, что он уже оценивал текущую статью
        :return: dict - данные формы
        """
        initial = super(DetailArticle, self).get_initial()
        current_article = str(DetailArticle.queryset.values('id')[0]['id'])
        cookies = self.request.COOKIES.get('likes', '')
        initial['like'] = True if current_article in cookies else False
        DetailArticle.checked = initial['like']
        return initial


class FavouriteView(ArticleView):
    """
    Обработка получения понравившихся статей
    """

    def get_queryset(self):
        """
        Получаем понравившиеся статьи путём фильрации объектов модели по id
        извлечёнными из cookies, если юзер не авторизован
        Если юзер залогинен, то добавляем из cookie товары в БД
        :return: QuerySet
        """
        favourites = self.request.COOKIES.get('likes', '').split(',')[:-1]
        current_user = self.request.user
        if current_user.is_authenticated:
            is_user_favourites = Favourites.objects.filter(who=current_user, article_id__in=favourites).exists()
            if len(favourites) != 0 and not is_user_favourites:
                Favourites.objects.bulk_create(Favourites(who=current_user, article_id=id) for id in favourites)
                return Article.objects.filter(favourites__who=current_user)
        return Article.objects.filter(id__in=favourites)


class CreateArticleView(LoginRequiredMixin, CreateView):
    """
    Обработка создния статьи
    """
    model = Article
    form_class = ArticleForm
    template_name = 'add.html'
    login_url = 'login'

    def get_success_url(self):
        return reverse('detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        """
        После успешной отправки (валидации) формы сохраняем данные статьи в БД
        :param form:
        :return:
        """
        article = form.save(commit=False)
        article.author = self.request.user
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
