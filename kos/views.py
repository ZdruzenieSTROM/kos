

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max, Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import AuthForm, EditTeamForm, RegisterForm
from .models import Game, Hint, Puzzle, Submission, Team, TeamMember, User


class GetTeamMixin:
    """Support for resolving team"""

    def get_team(self):
        """Resolve team from game and user"""
        # TODO: Allow multiple teams for user maybe
        return self.request.user.team


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
    login_url = reverse_lazy('kos:login')


class PuzzleView(UserPassesTestMixin, LoginRequiredMixin, DetailView, GetTeamMixin):
    model = Puzzle

    def test_func(self):
        puzzle = self.get_object()
        return self.get_team().current_level >= puzzle.level

    def get(self, request, *args, **kwargs):
        puzzle = self.get_object()
        return FileResponse(puzzle.file)


class GameView(LoginRequiredMixin, DetailView, GetTeamMixin):
    """View current game state"""
    model = Game
    template_name = 'kos/game.html'
    login_url = reverse_lazy('kos:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_team()
        puzzles = Puzzle.objects.filter(
            game=self.get_object(), level__lte=team.current_level).annotate(
                correctly_submitted=Max('submissions__correct')
        )
        for puzzle in puzzles:
            puzzle.current_submissions = puzzle.team_submissions(team)
        context['visible_puzzles'] = puzzles
        context['team'] = team
        return context

    def get_object(self):
        return self.get_team().game

    def post(self, request, *args, **kwargs):
        """Submit answer for puzzle"""
        team = self.get_team()
        puzzle_id = int(request.POST['puzzle'])
        answer = request.POST['answer']
        # Check if team can submit
        puzzle = Puzzle.objects.get(pk=puzzle_id)
        if puzzle.level > team.current_level:
            return HttpResponseForbidden()
        if puzzle.has_team_passed(team):
            is_correct = puzzle.check_unlock(answer)
            if is_correct:
                team.current_level = max(puzzle.level+1, team.current_level)
                team.save()
            return super().get(request, *args, **kwargs)

        # Check answer
        is_correct = puzzle.check_solution(answer)
        Submission.objects.create(
            puzzle=puzzle,
            team=team,
            competitor_answer=answer,
            correct=is_correct
        )
        if is_correct and team.is_online:
            team.current_level = max(puzzle.level+1, team.current_level)
            team.save()

        return super().get(request, *args, **kwargs)


class GameResultsView(DetailView):
    model = Game
    template_name = 'kos/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.request.user.team.game
        results = game.team_set.annotate(
            solved_puzzles=Count('submissions', filter=Q(
                submissions__correct=True)),
            last_correct_submission=Max(
                'submissions__submitted_at', filter=Q(submissions__correct=True))
        ).order_by('solved_puzzles', 'last_correct_submission')
        context['online_teams'] = results.filter(is_online=True)
        context['offline_teams'] = results.filter(is_online=False)
        return context


class HintView(UserPassesTestMixin, DetailView, GetTeamMixin):
    model = Hint

    def test_func(self):
        hint = self.get_object()
        team = self.get_team()
        time_to_take = hint.get_time_to_take(team)
        return (
            time_to_take is not None
            and time_to_take > 0
            and not team.hints_taken.filter(pk=hint.pk).exists()
            and not team.submissions.filter(correct=True, puzzle=hint.puzzle).exists()
        )

    def post(self, request, *args, **kwargs):
        self.get_team().hints_taken.add(self.get_object())

        return redirect('kos:game')


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
