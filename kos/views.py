

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from allauth.account.utils import send_email_confirmation
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Count, Max, Q
from django.dispatch import receiver
from django.http import FileResponse
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


@receiver(email_confirmed)  # Signal sent to activate user upon confirmation
def email_confirmed_(request, email_address, **kwargs):
    user = User.objects.get(email=email_address.email)
    user.is_active = True
    user.save()
    # try:
    #     game = Game.get_current()
    #     # create_invoice(user,game)
    # except Game.DoesNotExist:
    #     pass


@login_required
def logout_view(request):
    """Odhlásenie"""
    logout(request)
    return redirect('kos:game')


class GetTeamMixin(LoginRequiredMixin):
    """Support for resolving team"""
    login_url = reverse_lazy('kos:login')

    def get_team(self):
        """Resolve team from game and user"""
        # TODO: Allow multiple teams for user maybe
        return self.request.user.team


class LoginFormView(LoginView):
    """Prihlasovací formulár"""
    authentication_form = AuthForm
    next_page = reverse_lazy('kos:game')
    template_name = 'kos/login.html'


@login_required
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
        try:
            user = User.objects.create_user(email, email, password)
            user.is_active = False
            user.save()
            EmailAddress.objects.create(
                user=user, email=email, primary=True, verified=False)
        except IntegrityError:
            messages.error(
                self.request, 'Užívateľ s týmto emailom už existuje')
            return super().form_invalid(form)
        team = Team.objects.create(
            name=team_name,
            user=user,
            game=form.cleaned_data['game'],
            is_online=form.cleaned_data['is_online'],
            email=email
        )
        if (team.is_online and team.game.price_online == 0) or (
            not team.is_online and team.game.price_offline == 0
        ):
            team.paid = True
            team.save()
        for i in range(5):
            member_name = form.cleaned_data[f'team_member_{i+1}']
            if member_name is None or member_name == '':
                continue
            TeamMember.objects.create(
                name=member_name,
                team=team
            )
        send_email_confirmation(self.request, user, True)
        return super().form_valid(form)


class PuzzleView(UserPassesTestMixin, DetailView):
    """Vráti PDF so šifrou"""
    model = Puzzle

    def test_func(self):
        puzzle = self.get_object()
        team_year = None
        if self.request.user.is_authenticated:
            team_year = self.request.user.team.game.year
        if puzzle.game.year.solutions_public and (puzzle.game.year.is_public or puzzle.game.year == team_year):
            return True
        if not self.request.user.is_authenticated:
            return False
        team = self.request.user.team
        return team.current_level >= puzzle.level and puzzle.can_team_see(team)

    def get(self, request, *args, **kwargs):
        puzzle = self.get_object()
        return FileResponse(puzzle.file)


class PuzzleSolutionView(UserPassesTestMixin, DetailView):
    """Vráti PDF so šifrou"""
    model = Puzzle

    def test_func(self):
        puzzle = self.get_object()
        team_year = None
        if self.request.user.is_authenticated:
            team_year = self.request.user.team.game.year
        return puzzle.game.year.solutions_public and (puzzle.game.year.is_public or puzzle.game.year == team_year)

    def get(self, request, *args, **kwargs):
        puzzle = self.get_object()
        return FileResponse(puzzle.pdf_solution)


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
            # Before game end
            return redirect('kos:game')
        return response


class GameView(GetTeamMixin, DetailView):
    """View current game state"""
    model = Game
    template_name = 'kos/game.html'
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
            messages.error(request, 'Odpoveď nie je možné odovzdať')
            return redirect('kos:game')
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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None or not self.object.is_public:
            # Will redirect forever if there are no public years
            return redirect('kos:results-latest')
        context = self.get_context_data(object=object)
        return self.render_to_response(context)

    def add_places(self, results):
        current_place = 1
        previous_last_correct_submission = None
        previous_level = None
        results_list = []
        for i, result_row in enumerate(results):
            if previous_last_correct_submission != result_row.last_correct_submission \
                    or previous_level != result_row.current_level:
                current_place = i+1
                previous_last_correct_submission = result_row.last_correct_submission
                previous_level = result_row.current_level
            result_row.place = current_place
            results_list.append(result_row)
        return results_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = []
        context['years'] = Year.objects.filter(is_public=True)
        if self.object is None:
            return context
        for game in self.object.games.all():
            game_results = {}
            results = game.team_set.annotate(
                last_correct_submission=Max(
                    'submissions__submitted_at', filter=Q(submissions__correct=True, submissions__is_submitted_as_unlock_code=False))
            ).order_by('-current_level', 'last_correct_submission')
            game_results['online_teams'] = self.add_places(
                results.filter(is_online=True))
            game_results['offline_teams'] = self.add_places(
                results.filter(is_online=False))
            game_results['name'] = str(game)
            context['games'].append(game_results)

        return context


class HintView(GetTeamMixin, UserPassesTestMixin,  DetailView):
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

    def handle_no_permission(self):
        object_name = 'Nápovedu' if self.get_object().count_as_penalty else 'Riešenie'
        messages.error(self.request, f'{object_name} nie je možné zobrať')
        return redirect('kos:game')


class ResultsLatexExportView(ResultsView):
    """Results for pdf"""
    template_name = 'kos/results.tex'


class ResultsLatestView(ResultsView):
    """Výsledky poslednej šiforvačky"""
    template_name = 'kos/results.html'

    def get_object(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return self.request.user.team.game.year
        return Year.objects.filter(
            is_public=True).order_by('-end').first()


class ArchiveView(ListView):
    """Archive of old games"""
    template_name = 'kos/archive.html'
    context_object_name = 'years'

    def get_queryset(self):
        queryset = Year.objects.filter(
            is_public=True).all()
        if self.request.user.is_authenticated:
            queryset |= Year.objects.filter(
                pk=self.request.user.team.game.year.pk).all()
        return queryset


class TeamInfoView(GetTeamMixin, FormView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paid'] = (
            self.request.user.team.paid
            if hasattr(self.request.user, 'team')
            and hasattr(self.request.user.team, 'paid') else False
        )
        context['disabled'] = self.get_team().game.year.start <= now()
        return context

    def post(self, request, *args, **kwargs):
        team = self.get_team()
        if team.game.year.start <= now():
            messages.error(
                request, 'Tieto údaje nie je možné meniť po začiatku hry')
            return redirect('kos:change-profile')
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        team = self.get_team()
        if team.game.year.start <= now():
            for field in form.fields.values():
                field.widget.attrs['disabled'] = True
        return form

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
