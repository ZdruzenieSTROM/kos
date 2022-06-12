from django.urls import path
from django.urls import re_path as url

from . import views

urlpatterns = [
    path('register', views.SignUpView.as_view(), name='registration'),
    # path('login'),
    path('game', views.GameView.as_view(), name='game'),
]
