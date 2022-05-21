from django.urls import path
from .views import *


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('signup/', RegisterView.as_view(), name='signup'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('', ArticleView.as_view(), name='index'),
    path('favourites/', FavouriteView.as_view(), name='favourites'),
    path('preferences/', SettingsView.as_view(), name='preferences'),
    path('add/', CreateArticleView.as_view(), name='add'),
    path('<slug:slug>/', DetailArticle.as_view(), name='detail'),
]
