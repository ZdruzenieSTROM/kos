
from django.urls import path
from django.urls import re_path as url

from . import views

app_name = 'mas-problem'

urlpatterns = [
    path('main/', views.say_hello),
    url('login/', views.login_request, name='login'),
    url('register/', views.user_register, name='user_register'),
    path('logout/', views.logout_request, name="logout"),
    url('users/', views.users_list, name='users_list'),
    url('sutaz/', views.sutaz, name='sutaz')
]
