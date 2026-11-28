from datetime import timedelta
from io import StringIO
from unittest import mock

from allauth.account.models import EmailAddress
from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from kos.emails import html_to_text
from kos.forms import RegisterForm
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


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com')
class TeamBulkEmailTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'pass')
        self.client.force_login(self.admin)
        year = Year.objects.create(
            name='2026', start=now(), end=now() + timedelta(hours=5),
            registration_deadline=now(), contact_email='contact@example.com')
        self.game = Game.objects.create(name='Hra', year=year)

        self.user_verified = User.objects.create_user(
            'a@example.com', 'a@example.com', 'x')
        EmailAddress.objects.create(
            user=self.user_verified, email='a@example.com', verified=True, primary=True)
        self.user_unverified = User.objects.create_user(
            'b@example.com', 'b@example.com', 'x')
        EmailAddress.objects.create(
            user=self.user_unverified, email='b@example.com', verified=False, primary=True)

        self.team_own_email = Team.objects.create(
            name='Own', game=self.game, user=self.user_verified, email='team@example.com')
        self.team_user_email = Team.objects.create(
            name='UserMail', game=self.game, user=self.user_unverified)
        self.team_no_email = Team.objects.create(name='NoMail', game=self.game)
        self.url = reverse('admin:kos_team_changelist')

    def _post(self, teams, **extra):
        data = {
            'action': 'send_email',
            helpers.ACTION_CHECKBOX_NAME: [t.pk for t in teams],
            **extra,
        }
        return self.client.post(self.url, data, follow=True)

    def _login_staff_with(self, *codenames):
        staff = User.objects.create_user(
            'staff', 'staff@example.com', 'x', is_staff=True)
        staff.user_permissions.set(Permission.objects.filter(
            content_type__app_label='kos', codename__in=codenames))
        self.client.force_login(staff)

    def test_view_only_staff_cannot_send(self):
        self._login_staff_with('view_team')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        action_form = response.context['action_form']
        if action_form is not None:
            self.assertNotIn(
                'send_email', dict(action_form.fields['action'].choices))
        self._post([self.team_own_email], apply='1',
                   subject='Info', body='<p>Ahoj</p>')
        self.assertEqual(len(mail.outbox), 0)

    def test_staff_with_change_permission_can_send(self):
        self._login_staff_with('view_team', 'change_team')
        self._post([self.team_own_email], apply='1',
                   subject='Info', body='<p>Ahoj</p>')
        self.assertEqual(len(mail.outbox), 1)

    def test_contact_email_fallback(self):
        self.assertEqual(self.team_own_email.contact_email, 'team@example.com')
        self.assertEqual(self.team_user_email.contact_email, 'b@example.com')
        self.assertIsNone(self.team_no_email.contact_email)

    def test_intermediate_page_lists_recipients(self):
        teams = [self.team_own_email, self.team_user_email, self.team_no_email]
        response = self._post(teams)
        self.assertTemplateUsed(response, 'admin/kos/team/send_email.html')
        self.assertContains(response, 'team@example.com')
        self.assertContains(response, 'b@example.com')
        self.assertContains(response, 'bez emailovej adresy')
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_one_email_per_team(self):
        teams = [self.team_own_email, self.team_user_email, self.team_no_email]
        body = '<p>Ahoj <strong>tím</strong>, viac na <a href="https://kos.strom.sk">webe</a>.</p>'
        response = self._post(teams, apply='1', subject='Info', body=body)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox), ['b@example.com', 'team@example.com'])
        for message in mail.outbox:
            self.assertEqual(len(message.to), 1)
            self.assertEqual(message.cc, [])
            self.assertEqual(message.subject, 'Info')
            self.assertEqual(
                message.body, 'Ahoj tím, viac na webe (https://kos.strom.sk).')
            html, mimetype = message.alternatives[0]
            self.assertEqual(mimetype, 'text/html')
            self.assertIn(body, html)
            self.assertEqual(message.from_email, 'noreply@example.com')
            self.assertEqual(message.reply_to, ['contact@example.com'])
        self.assertContains(response, 'Odoslané emaily: 2')
        self.assertContains(response, 'NoMail')

    def test_shared_address_receives_one_email(self):
        twin = Team.objects.create(
            name='Twin', game=self.game, email='TEAM@example.com ')
        teams = [self.team_own_email, twin, self.team_user_email]
        response = self._post(teams)
        self.assertContains(response, 'nepošle sa znova', count=1)
        response = self._post(teams, apply='1', subject='Info', body='<p>Ahoj</p>')
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            sorted(m.to[0].lower() for m in mail.outbox),
            ['b@example.com', 'team@example.com'])
        self.assertContains(response, 'Odoslané emaily: 2')
        self.assertContains(response, 'email poslaný iba raz')

    def test_empty_html_body_is_invalid(self):
        response = self._post(
            [self.team_own_email], apply='1', subject='Info', body='<p><br></p>')
        self.assertTemplateUsed(response, 'admin/kos/team/send_email.html')
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_form_does_not_send(self):
        response = self._post([self.team_own_email], apply='1', subject='', body='')
        self.assertTemplateUsed(response, 'admin/kos/team/send_email.html')
        self.assertEqual(len(mail.outbox), 0)

    def test_email_confirmed_filter(self):
        response = self.client.get(self.url, {'email_confirmed': 'yes'})
        self.assertEqual(
            list(response.context['cl'].queryset), [self.team_own_email])
        response = self.client.get(self.url, {'email_confirmed': 'no'})
        self.assertEqual(
            set(response.context['cl'].queryset),
            {self.team_user_email, self.team_no_email})


class HtmlToTextTests(TestCase):
    def test_formatting_and_lists(self):
        html = ('<h2>Info</h2><p>Riadok <em>jeden</em><br>riadok dva</p>'
                '<ul><li>prvý</li><li>druhý</li></ul>'
                '<ol><li>a</li><li>b</li></ol>'
                '<p><a href="https://x.sk">https://x.sk</a> &amp; koniec</p>')
        self.assertEqual(
            html_to_text(html),
            'Info\n\nRiadok jeden\nriadok dva\n\n- prvý\n- druhý\n\n'
            '1. a\n2. b\n\nhttps://x.sk & koniec')
