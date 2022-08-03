from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import AuthForm, EditTeamForm, RegisterForm
from .models import Game, Puzzle, Team, TeamMember, User


class LoginFormView(LoginView):
    """Prihlasovací formulár"""
    authentication_form = AuthForm
    next_page = reverse_lazy('kos:game')
    template_name = 'kos/login.html'


class SignUpView(FormView):
    """Registračný formulár"""
    form_class = RegisterForm
    next_page = reverse_lazy("kos:login")
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
            is_online=form.cleaned_data['is_online'],
            category=form.cleaned_data['category']
        )
        for i in range(5):
            member_name = form.cleaned_data[f'team_member_{i+1}']
            TeamMember.objects.create(
                name=member_name,
                team=team
            )
        return super().form_valid(form)


class GameIntroductionView(DetailView):
    template_name = 'kos/game_intro.html'
    model = Game


class GameView(LoginRequiredMixin, DetailView):
    """View current game state"""
    model = Game
    template_name = 'kos/game.html'
    login_url = reverse_lazy('kos:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.request.user.team
        context['visible_puzzles'] = Puzzle.objects.filter(
            game=self.get_object(), level__lte=team.current_level).prefetch_related()
        return context

    def get_object(self):
        user = self.request.user
        return user.team.game


class GameResultsView(DetailView):
    """Results of a game"""


class GameResultsExportView(DetailView):
    """Results for pdf"""


class HistoryGameView(ListView):
    """Archive of old games"""
    queryset = Game.objects.filter(end__lte=now())


class TeamInfoView(FormView):
    """Team profile"""
    form_class = EditTeamForm
    success_url = reverse_lazy("change-profile")
    template_name = "kos/change_profile.html"


def submit():
    """Submit puzzle solution"""
