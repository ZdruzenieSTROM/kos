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
