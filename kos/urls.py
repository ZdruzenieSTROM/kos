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
    path(r'statistiky/<int:pk>', views.StatisticsView.as_view(), name='statistics'),
    #     path('statistiky/aktualne', views.StatisticsView.as_view,
    #          name='statistics-latest'),
    path(r'poradie-latex/<int:pk>',
         views.ResultsLatexExportView.as_view(), name='results-latex'),
    path('pravidla', flatpage, {'url': '/pravidla/'}, name='rules'),
    path('pokyny', flatpage, {'url': '/pokyny/'}, name='info'),
    path('archiv', views.ArchiveView.as_view(), name='archive'),
    path(r'archiv-sifier/<int:pk>',
         views.PuzzleArchiveView.as_view(), name='puzzle-archive'),
    path('archiv-sifier/aktualne',
         views.PuzzleArchiveLatest.as_view(), name='puzzle-archive-latest'),
    path(r'hint/<int:pk>', views.HintView.as_view(), name='hint'),
    path(r'skip/<int:pk>', views.SkipPuzzleView.as_view(), name='skip'),
    path(r'sifra/<int:pk>', views.PuzzleView.as_view(), name='puzzle'),
    path(r'riesenie-sifry/<int:pk>',
         views.PuzzleSolutionView.as_view(), name='puzzle-solution'),

]
