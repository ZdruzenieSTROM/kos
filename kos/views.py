

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count, Max, Q
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import DetailView, FormView, ListView

from .forms import AuthForm, ChangePasswordForm, EditTeamForm, RegisterForm
from .models import (Game, Hint, Puzzle, Submission, Team, TeamMember, User,
                     Year)


def view_404(request, exception=None):  # pylint: disable=unused-argument
    """Presmerovanie 404 na homepage"""
    return redirect('kos:home')


def logout_view(request):
    """Odhlásenie"""
    logout(request)
    return redirect('kos:game')


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

# TODO: Login required


def change_password(request):
    """Zmena hesla"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Heslo bolo zmenené!')
            return redirect('kos:change-password')
        messages.error(request, 'Chyba pri zmene hesla')
    else:
        form = ChangePasswordForm(request.user)
    return render(request, 'kos/change_password.html', {
        'form': form
    })


class SignUpView(FormView):
    """Registračný formulár"""
    form_class = RegisterForm
    next_page = reverse_lazy("kos:login")
    success_url = reverse_lazy("kos:game")
    template_name = "kos/registration.html"

    def form_valid(self, form):
        team_name = form.cleaned_data['team_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = User.objects.create_user(team_name, email, password)
        team = Team.objects.create(
            name=team_name,
            user=user,
            game=form.cleaned_data['game'],
            is_online=form.cleaned_data['is_online']
        )
        for i in range(5):
            member_name = form.cleaned_data[f'team_member_{i+1}']
            if member_name is None or member_name == '':
                continue
            TeamMember.objects.create(
                name=member_name,
                team=team
            )
        return super().form_valid(form)


class GameIntroductionView(DetailView):
    """Informácie pred hrou. Zobrazia sa ak hra ešte nezačala"""
    template_name = 'kos/game_intro.html'
    model = Game
    login_url = reverse_lazy('kos:login')


class PuzzleView(UserPassesTestMixin, LoginRequiredMixin, DetailView, GetTeamMixin):
    """Vráti PDF so šifrou"""
    model = Puzzle

    def test_func(self):
        puzzle = self.get_object()
        return self.get_team().current_level >= puzzle.level

    def get(self, request, *args, **kwargs):
        puzzle = self.get_object()
        return FileResponse(puzzle.file)


class PuzzleSolutionView(UserPassesTestMixin, LoginRequiredMixin, DetailView, GetTeamMixin):
    """Vráti PDF so šifrou"""
    model = Puzzle

    def test_func(self):
        puzzle = self.get_object()
        return puzzle.game.year.solutions_public

    def get(self, request, *args, **kwargs):
        puzzle = self.get_object()
        return FileResponse(puzzle.solution)


class BeforeGameView(LoginRequiredMixin, DetailView):
    """Zobrazí sa tímu pred začiatkom hry"""
    model = Game
    template_name = 'kos/before_game.html'
    login_url = reverse_lazy('kos:login')
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.year.start <= now():
            # After game start
            return redirect('kos:game')
        return response


class AfterGameView(LoginRequiredMixin, DetailView):
    """Zobrazí sa tímu po konci hry"""
    model = Game
    template_name = 'kos/after_game.html'
    login_url = reverse_lazy('kos:login')
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.year.end >= now():
            # After game start
            return redirect('kos:game')
        return response


class GameView(LoginRequiredMixin, DetailView, GetTeamMixin):
    """View current game state"""
    model = Game
    template_name = 'kos/game.html'
    login_url = reverse_lazy('kos:login')
    context_object_name = 'game'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.year.start > now():
            # Pred začatím hry
            return redirect('kos:before-game', pk=self.object.pk)
        if self.object.year.end < now():
            # Po konci hry
            return redirect('kos:after-game', pk=self.object.pk)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_team()
        puzzles = Puzzle.objects.filter(
            game=self.object, level__lte=team.current_level).order_by('-level')
        if team.current_level > puzzles[0].level:
            context['message'] = self.object.final_message
        for puzzle in puzzles:
            # TODO: This probably can be done with annotate as a part of the first filter
            # but I couldn't make it work
            puzzle.correctly_submitted = puzzle.submissions.filter(
                team=team, correct=True, is_submitted_as_unlock_code=False).exists()
            puzzle.current_submissions = puzzle.team_submissions(
                team).order_by('-submitted_at')
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
        if not puzzle.can_team_submit(team):
            return HttpResponseForbidden()
        if not puzzle.can_team_see(team):
            is_correct = puzzle.check_unlock(answer)
            Submission.objects.create(
                puzzle=puzzle,
                team=team,
                competitor_answer=Puzzle.clean_text(answer),
                correct=is_correct,
                is_submitted_as_unlock_code=True
            )
            return redirect('kos:game')

        # Check answer
        is_correct = puzzle.check_solution(answer)
        Submission.objects.create(
            puzzle=puzzle,
            team=team,
            competitor_answer=Puzzle.clean_text(answer),
            correct=is_correct
        )
        if is_correct:
            team.current_level = max(puzzle.level+1, team.current_level)
            team.save()

        return redirect('kos:game')


class ResultsView(DetailView):
    """Výsledková listina"""
    model = Year
    template_name = 'kos/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = []
        for game in self.object.games.all():
            game_results = {}
            results = game.team_set.annotate(
                solved_puzzles=Count('submissions', filter=Q(
                    submissions__correct=True, submissions__is_submitted_as_unlock_code=False)),

                last_correct_submission=Max(
                    'submissions__submitted_at', filter=Q(submissions__correct=True, submissions__is_submitted_as_unlock_code=False))
            ).order_by('-solved_puzzles', 'last_correct_submission')
            game_results['online_teams'] = results.filter(is_online=True)
            game_results['offline_teams'] = results.filter(is_online=False)
            game_results['name'] = str(game)
            context['games'].append(game_results)
        context['years'] = Year.objects.filter(start__lte=now())
        return context


class HintView(UserPassesTestMixin, DetailView, GetTeamMixin):
    """Vezme hint"""
    model = Hint

    def test_func(self):
        hint = self.get_object()
        team = self.get_team()
        return hint.can_team_take(team)

    def post(self, request, *args, **kwargs):
        """Pridaj hint"""
        self.get_team().hints_taken.add(self.get_object())
        return redirect('kos:game')


class ResultsLatexExportView(ResultsView):
    """Results for pdf"""
    template_name = 'kos/results.tex'


class ResultsLatestView(ResultsView):
    """Výsledky poslednej šiforvačky"""
    template_name = 'kos/results.html'

    def get_object(self, *args, **kwargs):
        year = Year.objects.filter(
            is_public=True).order_by('-end').first()
        return year


class ArchiveView(ListView):
    """Archive of old games"""
    queryset = Year.objects.all()
    template_name = 'kos/archive.html'
    context_object_name = 'years'


class TeamInfoView(FormView, GetTeamMixin):
    """Team profile"""
    form_class = EditTeamForm
    success_url = reverse_lazy("kos:change-profile")
    template_name = "kos/change_profile.html"

    def get_initial(self):
        team = self.get_team()
        init_dict = {
            'is_online': team.is_online
        }
        for i, member in enumerate(team.members.all()):
            init_dict[f'team_member_{i+1}'] = member.name
        return init_dict

    def form_valid(self, form):
        team = self.get_team()
        team.members.all().delete()
        member_id = 1
        try:
            while True:
                if form.cleaned_data[f'team_member_{member_id}'] == '':
                    break
                team.members.add(
                    TeamMember(
                        name=form.cleaned_data[f'team_member_{member_id}']), bulk=False)
                member_id += 1
        except KeyError:
            pass
        return super().form_valid(form)
