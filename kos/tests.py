from datetime import timedelta
from io import StringIO

from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from kos.models import Game, Team, Year

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
