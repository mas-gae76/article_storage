from django.urls import path
from .views import *


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('signup/', RegisterView.as_view(), name='signup'),
]