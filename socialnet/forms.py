from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Article
from django import forms


class RegisterForm(UserCreationForm):
    """
    Форма для регистрации
    """
    password1 = forms.CharField(widget=forms.PasswordInput, label='Пароль', error_messages={
        'invalid': 'Пароль должен быть не менее 8 символов и не содержать только цифры'})
    password2 = forms.CharField(widget=forms.PasswordInput, label='Подтвердите пароль')

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def clean_password2(self):
        """
        Проверка соответствия повторного пароля
        :return: str - повторный пароль
        """
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают!\r\n Попытайтесь снова')
        return cd['password2']

    def clean_email(self):
        """
        Проверка ввода email (не должен существовать в БД)
        :return: str - email
        """
        cd = self.cleaned_data
        if User.objects.filter(email=cd['email']).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует!')
        return cd['email']


class LoginForm(AuthenticationForm):
    """
    Форма для входа
    """

    class Meta:
        model = User
        fields = ('username', 'password')


class ArticleForm(forms.ModelForm):
    """
    Форма для создания статьи
    Доступные поля: заголовок (транслитом), заголовок, краткое содержание, описание
    """

    class Meta:
        model = Article
        fields = ('slug', 'header', 'summary', 'description', )


class SettingForm(forms.Form):
    """
    Форма для настройки пагинации статей
    """
    paginate_by = forms.IntegerField(label='Кол-во статей на одной странице',
                                     initial=10,
                                     widget=forms.NumberInput,
                                     min_value=10, max_value=100)


class OrderAndFilterForm(forms.Form):
    """
    Форма для фильтрации статей по slug и для сортировки по дате и рейтингу
    """

    DATE_CHOICES = (
        ('-date', 'Самые новые статьи'),
        ('date', 'Самые старые статьи'),
        ('header', 'По умолчанию'),
    )

    RATING_CHOICES = (
        ('-rating', 'Самый высокий рейтинг'),
        ('rating', 'Самый низкий рейтинг'),
        ('header', 'По умолчанию'),
    )

    date_order = forms.ChoiceField(label='Сортировка по дате', choices=DATE_CHOICES, initial=DATE_CHOICES[2])
    rating_order = forms.ChoiceField(label='Сортировка по рейтингу', choices=RATING_CHOICES, initial=RATING_CHOICES[2])
    filter_by_slug = forms.SlugField(label='Поиск статьи по заголовку (транслитом)', required=False, initial='')


class FavouriteForm(forms.Form):
    """
    Форма для отметки понравившейся статьи
    """

    like = forms.ChoiceField(label='Понравилась?', widget=forms.CheckboxInput, required=False, initial=False)


class RateForm(forms.Form):
    """
    Форма для фиксации рейтинга статьи
    """

    RATING_CHOICES = (
        (-1, 'Плохо'),
        (0, 'Нейтрально'),
        (1, 'Хорошо')
    )

    rate = forms.ChoiceField(label='Оценить: ', required=False, choices=RATING_CHOICES, initial=RATING_CHOICES[1])
