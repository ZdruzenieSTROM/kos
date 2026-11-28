from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from kos.forms import RegisterForm
from kos.models import Game, Puzzle, PuzzleTeamState, Team, Year

User = get_user_model()


class DeleteTeamUsersTest(TestCase):
    """Mazanie používateľov tímov (admin akcie a management command)"""

    def setUp(self):
        year = Year.objects.create(
            name='2026', start=now() - timedelta(days=2),
            end=now() - timedelta(days=1),
            registration_deadline=now() - timedelta(days=3))
        self.game = Game.objects.create(name='Hra', year=year)
        self.other_game = Game.objects.create(name='Iná hra', year=year)
        self.user = User.objects.create_user(
            'tim', email='tim@example.com', password='x')
        self.team = Team.objects.create(
            name='Tím', user=self.user, game=self.game)
        self.other_user = User.objects.create_user(
            'iny', email='iny@example.com', password='x')
        self.other_team = Team.objects.create(
            name='Iný tím', user=self.other_user, game=self.other_game)
        self.admin = User.objects.create_superuser(
            'admin', email='admin@example.com', password='x')
        self.client.force_login(self.admin)

    def test_delete_user_keeps_team_and_email(self):
        self.assertTrue(self.team.delete_user())
        self.team.refresh_from_db()
        self.assertIsNone(self.team.user)
        self.assertEqual(self.team.email, 'tim@example.com')
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_user_skips_staff(self):
        self.user.is_staff = True
        self.user.save()
        self.assertFalse(self.team.delete_user())
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_game_action_requires_confirmation(self):
        url = reverse('admin:kos_game_changelist')
        data = {'action': 'delete_users',
                helpers.ACTION_CHECKBOX_NAME: [self.game.pk]}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Áno, zmazať')
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

        response = self.client.post(url, {**data, 'confirm': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other_user.pk).exists())

    def test_team_action(self):
        url = reverse('admin:kos_team_changelist')
        response = self.client.post(url, {
            'action': 'delete_users',
            helpers.ACTION_CHECKBOX_NAME: [self.other_team.pk],
            'confirm': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.other_user.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_management_command(self):
        call_command('deleteusers', self.game.pk, stdout=StringIO())
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other_user.pk).exists())


class RegistrationDeadlineTest(TestCase):
    """Registrácia sa musí uzavrieť po deadline, aj keď server beží
    od skôr (regresia pre issue #157)."""

    def setUp(self):
        current = now()
        self.year = Year.objects.create(
            name='Kos test',
            start=current + timedelta(days=7),
            end=current + timedelta(days=8),
            is_public=True,
            is_active=True,
            registration_deadline=current + timedelta(days=1),
        )
        self.game = Game.objects.create(name='Hlavná', year=self.year)
        self.after_deadline = current + timedelta(days=2)

    def form_data(self):
        return {
            'team_name': 'Neskorý tím',
            'email': 'late@example.com',
            'password': 'tajneheslo123',
            'password2': 'tajneheslo123',
            'team_member_1': 'Jano',
            'game': self.game.pk,
        }

    def test_game_offered_before_deadline(self):
        form = RegisterForm()
        self.assertIn(self.game, form.fields['game'].queryset)

    def test_game_not_offered_after_deadline(self):
        # Deadline prejde až po importe modulu s formulárom.
        with mock.patch('kos.forms.now', return_value=self.after_deadline):
            form = RegisterForm()
            self.assertNotIn(self.game, form.fields['game'].queryset)

    def test_form_invalid_after_deadline(self):
        with mock.patch('kos.forms.now', return_value=self.after_deadline):
            form = RegisterForm(data=self.form_data())
            self.assertFalse(form.is_valid())
            self.assertIn('game', form.errors)

    def test_signup_view_rejects_after_deadline(self):
        with mock.patch('kos.forms.now', return_value=self.after_deadline):
            response = self.client.post(
                reverse('kos:registration'), self.form_data())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Team.objects.exists())
        self.assertFalse(
            get_user_model().objects.filter(email='late@example.com').exists())


class OnlineLockAfterDeadlineTest(TestCase):
    """Po deadline registrácie sa is_online nesmie dať zmeniť ani
    podvrhnutým requestom (regresia pre issue #158)."""

    def setUp(self):
        current = now()
        year = Year.objects.create(
            name='Kos test',
            start=current + timedelta(days=1),
            end=current + timedelta(days=2),
            is_public=True,
            is_active=True,
            registration_deadline=current - timedelta(days=1),
        )
        Game.objects.create(name='Hlavná', year=year)
        self.user = get_user_model().objects.create_user(
            'team@example.com', 'team@example.com', 'tajneheslo123')
        self.client.force_login(self.user)
        self.url = reverse('kos:change-profile')

    def make_team(self, is_online):
        return Team.objects.create(
            name='Tím', user=self.user, game=Game.objects.get(),
            is_online=is_online, email=self.user.email)

    def test_offline_team_cannot_switch_to_online(self):
        team = self.make_team(is_online=False)
        self.client.post(self.url, {
            'team_name': 'Tím', 'team_member_1': 'Jano', 'is_online': 'on'})
        team.refresh_from_db()
        self.assertFalse(team.is_online)

    def test_online_team_stays_online_without_is_online_in_post(self):
        # Prehliadač disabled pole neodošle - tím nesmie spadnúť na offline.
        team = self.make_team(is_online=True)
        self.client.post(self.url, {
            'team_name': 'Tím', 'team_member_1': 'Jano'})
        team.refresh_from_db()
        self.assertTrue(team.is_online)
        self.assertEqual(
            list(team.members.values_list('name', flat=True)), ['Jano'])

    def test_is_online_rendered_disabled(self):
        self.make_team(is_online=True)
        response = self.client.get(self.url)
        self.assertTrue(response.context['form'].fields['is_online'].disabled)


class SubmitAfterGameEndTest(TestCase):
    """Po konci hry sa nesmie dať odovzdať riešenie, ani keď má tím
    ešte načítanú stránku (regresia pre issue #152)."""

    def setUp(self):
        current = now()
        self.year = Year.objects.create(
            name='Kos test',
            start=current - timedelta(hours=5),
            end=current + timedelta(hours=1),
            is_public=True,
            is_active=True,
            registration_deadline=current - timedelta(days=1),
        )
        self.game = Game.objects.create(name='Hlavná', year=self.year)
        self.puzzle = Puzzle.objects.create(
            name='Šifra', game=self.game, solution='RIESENIE',
            unlock_code='KOD', file='zadanie.pdf', level=1,
            skip_allowed_after=timedelta(0))
        self.user = User.objects.create_user(
            'team@example.com', 'team@example.com', 'tajneheslo123')
        self.team = Team.objects.create(
            name='Tím', user=self.user, game=self.game, is_online=True)
        PuzzleTeamState.get_or_create(team=self.team, puzzle=self.puzzle)
        self.client.force_login(self.user)

    def end_game(self):
        self.year.end = now() - timedelta(minutes=1)
        self.year.save()

    def test_can_submit_during_game(self):
        self.assertTrue(self.puzzle.can_team_submit(self.team))
        self.assertTrue(self.puzzle.can_team_skip(self.team))

    def test_cannot_submit_or_skip_after_end(self):
        self.end_game()
        self.puzzle.refresh_from_db()
        self.assertFalse(self.puzzle.can_team_submit(self.team))
        self.assertFalse(self.puzzle.can_team_skip(self.team))

    def test_post_after_end_is_rejected(self):
        self.end_game()
        self.client.post(reverse('kos:game'), {
            'answer': 'RIESENIE', 'puzzle': self.puzzle.pk})
        state = PuzzleTeamState.objects.get(
            team=self.team, puzzle=self.puzzle)
        self.assertFalse(state.solved)
        self.assertFalse(state.submissions.exists())
        self.team.refresh_from_db()
        self.assertEqual(self.team.current_level, 1)
