from datetime import timedelta

from allauth.account.models import EmailAddress
from django.contrib.admin import helpers
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now

from kos.emails import html_to_text
from kos.models import Game, Team, Year

User = get_user_model()


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
