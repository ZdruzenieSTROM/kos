from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from kos.forms import RegisterForm
from kos.models import Game, Team, Year


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
