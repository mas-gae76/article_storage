from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, reverse
from django.views.generic import CreateView

from .forms import RegisterForm, LoginForm


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return render(self.request, 'index.html', context={'user': user})


class UserLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm

    def form_valid(self, form):
        cd = form.cleaned_data
        user = authenticate(self.request, email=cd['username'], password=cd['password'])
        login(self.request, user)
        return redirect(reverse('index'))
