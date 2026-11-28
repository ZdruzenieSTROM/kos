"""Regressions for the Django/allauth dependency upgrade."""
import re
from datetime import timedelta
from urllib.parse import urlsplit

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now


class AccountCompatibilityTests(TestCase):
    def test_registration_confirmation_activates_user(self):
        self.prepare_registration()
        response = self.client.post(reverse('kos' + ':registration'), self.registration)
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='upgrade@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://[^\s<>]+/accounts/confirm-email/[^\s<>]+', mail.outbox[0].body).group()
        response = self.client.get(urlsplit(url).path)
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(EmailAddress.objects.get(user=user).verified)

    def test_custom_password_reset_completes(self):
        user = get_user_model().objects.create_user('reset@example.com', 'reset@example.com', 'old-password')
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        response = self.client.post(reverse('account_reset_password'), {'email': user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        url = re.search(r'https?://[^\s<>]+/password/reset/[^\s<>]+', mail.outbox[0].body).group()
        response = self.client.get(urlsplit(url).path, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(response.request['PATH_INFO'], {'password1': 'new-strong-password-2026', 'password2': 'new-strong-password-2026'})
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password('new-strong-password-2026'))

    def prepare_registration(self):
        from kos.models import Game, Year
        start = now()
        year = Year.objects.create(name='Upgrade', start=start, end=start + timedelta(hours=1), registration_deadline=start + timedelta(hours=1), is_active=True)
        game = Game.objects.create(name='Upgrade', year=year)
        self.registration = dict(team_name='Upgrade', email='upgrade@example.com', password='password', password2='password', team_member_1='Tester', game=game.pk, is_online=True)


class MigrationBranchCompatibilityTests(TestCase):
    def test_overlapping_branches_migrate_in_either_order(self):
        import os
        import subprocess
        import sys
        import textwrap

        branches = [
            '0029_game_frozen_results_json_team_is_public_and_more',
            '0029_remove_submission_correct_remove_submission_puzzle_and_more',
        ]
        for first, second in [branches, list(reversed(branches))]:
            with self.subTest(first=first):
                code = textwrap.dedent("""
                    import django
                    from django.conf import settings
                    settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
                    django.setup()
                    from django.db import connection
                    from django.db.migrations.executor import MigrationExecutor
                    import sys
                    first, second = sys.argv[1:]
                    MigrationExecutor(connection).migrate([('kos', first)])
                    MigrationExecutor(connection).migrate([('kos', first), ('kos', second)])
                    MigrationExecutor(connection).migrate([('kos', '0035_alter_puzzleteamstate_started_at_and_more')])
                    with connection.cursor() as cursor:
                        columns = connection.introspection.get_table_description(cursor, 'kos_year')
                    assert sum(c.name == 'photo_url' for c in columns) == 1
                """)
                result = subprocess.run([sys.executable, '-c', code, first, second], capture_output=True, text=True, env=os.environ.copy())
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
