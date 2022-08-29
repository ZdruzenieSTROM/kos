from django.contrib.flatpages.views import flatpage
from django.urls import path

from . import views

app_name = 'kos'

urlpatterns = [
    path('', flatpage, {'url': '/pravidla/'}, name='home'),
    path('register', views.SignUpView.as_view(), name='registration'),
    path('change-profile', views.TeamInfoView.as_view(), name='change-profile'),
    path('change-password', views.GameIntroductionView.as_view(),
         name='change-password'),
    path('login', views.LoginFormView.as_view(), name='login'),
    path('logout', views.logout_view, name='logout'),
    path('game', views.GameView.as_view(), name='game'),
    path(r'results/<int:pk>', views.ResultsView.as_view(), name='results'),
    path('results/latest', views.ResultsLatestView.as_view(),
         name='results-latest'),
    path(r'results-latex/<int:pk>',
         views.ResultsLatexExportView.as_view(), name='results-latex'),
    path('pravidla', flatpage, {'url': '/pravidla/'}, name='rules'),
    path('archive', views.HistoryGameView.as_view(), name='archive'),
    path(r'hint/<int:pk>', views.HintView.as_view(), name='hint'),
    path(r'puzzle/<int:pk>', views.PuzzleView.as_view(), name='puzzle'),

]
