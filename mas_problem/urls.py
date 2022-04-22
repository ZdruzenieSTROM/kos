"""online_competitions URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.urls import re_path as url
from . import views

urlpatterns = [
    path('main/', views.say_hello),
    url('login/', views.login_request, name='login'),
    url('register/', views.user_register, name='user_register'),
    path("logout/", views.logout_request, name= "logout"),
    url('users/', views.users_list, name='users_list'),
    url('sutaz/', views.sutaz, name='sutaz')
]
