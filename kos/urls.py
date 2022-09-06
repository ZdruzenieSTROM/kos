from django.contrib.flatpages.views import flatpage
from django.urls import path

from . import views

app_name = 'kos'

urlpatterns = [
    path('', flatpage, {'url': '/pravidla/'}, name='home'),
    path('registracia', views.SignUpView.as_view(), name='registration'),
    path('zmena-profilu', views.TeamInfoView.as_view(), name='change-profile'),
    path('zmena-hesla', views.change_password,
         name='change-password'),
    path('prihlasenie', views.LoginFormView.as_view(), name='login'),
    path('odhlasenie', views.logout_view, name='logout'),
    path('pred-hrou/<int:pk>', views.BeforeGameView.as_view(), name='before-game'),
    path('po-hre/<int:pk>', views.AfterGameView.as_view(), name='after-game'),
    path('hra', views.GameView.as_view(), name='game'),
    path(r'poradie/<int:pk>', views.ResultsView.as_view(), name='results'),
    path('poradie/aktualne', views.ResultsLatestView.as_view(),
         name='results-latest'),
    path(r'poradie-latex/<int:pk>',
         views.ResultsLatexExportView.as_view(), name='results-latex'),
    path('pravidla', flatpage, {'url': '/pravidla/'}, name='rules'),
    path('archiv', views.ArchiveView.as_view(), name='archive'),
    path(r'hint/<int:pk>', views.HintView.as_view(), name='hint'),
    path(r'sifra/<int:pk>', views.PuzzleView.as_view(), name='puzzle'),
    path(r'riesenie-sifry/<int:pk>',
         views.PuzzleSolutionView.as_view(), name='puzzle-solution'),

]
