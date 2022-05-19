from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django import forms


class RegisterForm(UserCreationForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Пароль', error_messages={
        'invalid': 'Пароль должен быть не менее 8 символов и не содержать только цифры'})
    password2 = forms.CharField(widget=forms.PasswordInput, label='Подтвердите пароль')

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают!\r\n Попытайтесь снова')
        return cd['password2']

    def clean_email(self):
        cd = self.cleaned_data
        if User.objects.filter(email=cd['email']).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует!')
        return cd['email']


class LoginForm(AuthenticationForm):

    class Meta:
        model = User
        fields = ('username', 'password')