from django.urls import path

from . import views

app_name = 'kos'

urlpatterns = [
    path('register', views.SignUpView.as_view(), name='registration'),
    path('change-profile', views.TeamInfoView.as_view(), name='change-profile'),
    path('change-password', views.GameIntroductionView.as_view(),
         name='change-password'),
    path('login', views.LoginFormView.as_view(), name='login'),
    path('game', views.GameView.as_view(), name='game'),
    path('game-intro', views.GameIntroductionView.as_view(), name='game-intro'),
    path('results', views.GameView.as_view(), name='results')

]
