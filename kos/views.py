from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import RegisterForm
from .models import Game, Puzzle, Team, TeamMember, User

# Create your views here.


class SignUpView(FormView):
    form_class = RegisterForm
    success_url = reverse_lazy("kos-login")
    template_name = "kos/registration.html"

    def form_valid(self, form):
        team_name = form.cleaned_data['team_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(team_name, email, password)
        team = Team.objects.create(
            name=team_name,
            user=user,
            game=Game.objects.first(),
            is_online=True,  # TODO: Change
            category=None  # TODO: Change
        )
        for i in range(5):
            member_name = form.cleaned_data[f'team_member{i+1}']
            TeamMember.objects.create(
                name=member_name,
                team=team
            )
        return super().form_valid(form)


class GameView(DetailView):
    """View current game state"""
    model = Game

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = Team.objects.get()
        context['visible_puzzles'] = Puzzle.objects.filter(
            game=self.get_object(), level__lte=team.current_level).prefetch_related()
        return context


class GameResultsView(DetailView):
    """Results of a game"""


class GameResultsExportView(DetailView):
    """Results for pdf"""


class HistoryGameView(ListView):
    """Archive of old games"""
    queryset = Game.objects.filter(end__lte=now())


class TeamInfoView(DetailView):
    """Team profile"""


def submit():
    """Submit puzzle solution"""
    pass
