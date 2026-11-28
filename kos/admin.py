"""Admin for Kos app"""
import json

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.response import TemplateResponse

from kos import models
from kos.emails import html_to_text, wrap_html

# pylint: disable=missing-docstring


def delete_team_users(modeladmin, request, selected, teams):
    """
    Spoločná logika pre admin akcie na zmazanie používateľov tímov.
    Najprv zobrazí potvrdzovaciu stránku, po potvrdení používateľov zmaže."""
    teams = teams.select_related('user', 'game')
    if request.POST.get('confirm'):
        deleted = sum(1 for team in teams if team.delete_user())
        modeladmin.message_user(
            request, f'Zmazaných používateľov: {deleted}', messages.SUCCESS)
        return None

    teams_with_user = [team for team in teams if team.user is not None]
    context = {
        **modeladmin.admin_site.each_context(request),
        'title': 'Zmazať používateľov tímov',
        'opts': modeladmin.model._meta,
        'queryset': selected,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'action': request.POST.get('action'),
        'to_delete': [team for team in teams_with_user
                      if not (team.user.is_staff or team.user.is_superuser)],
        'skipped': [team for team in teams_with_user
                    if team.user.is_staff or team.user.is_superuser],
    }
    return TemplateResponse(
        request, 'admin/kos/delete_team_users_confirmation.html', context)


class TeamMemberInline(admin.TabularInline):
    model = models.TeamMember


class EmailConfirmedFilter(admin.SimpleListFilter):
    title = 'email potvrdený'
    parameter_name = 'email_confirmed'

    def lookups(self, request, model_admin):
        return (('yes', 'Áno'), ('no', 'Nie'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user__emailaddress__verified=True).distinct()
        if self.value() == 'no':
            return queryset.exclude(user__emailaddress__verified=True)
        return queryset


class TeamEmailForm(forms.Form):
    subject = forms.CharField(label='Predmet', max_length=200)
    body = forms.CharField(label='Text správy', widget=forms.Textarea(
        attrs={'rows': 15, 'cols': 80, 'class': 'rich-text-source'}))

    def clean_body(self):
        body = self.cleaned_data['body']
        if not html_to_text(body):
            raise forms.ValidationError('Text správy nesmie byť prázdny.')
        return body


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'is_online', 'paid')
    list_filter = ('game', 'is_online', 'paid', EmailConfirmedFilter)
    inlines = [TeamMemberInline]

    actions = ['send_email', 'delete_users']

    @admin.action(description='Zmaž používateľov vybraných tímov',
                  permissions=['delete'])
    def delete_users(self, request, queryset):
        """Zmaže používateľov vybraných tímov"""
        return delete_team_users(self, request, queryset, queryset)

    @admin.action(description='Poslať email vybraným tímom')
    def send_email(self, request, queryset):
        """Pošle email každému vybranému tímu zvlášť"""
        teams = list(queryset.select_related('user', 'game__year'))
        form = TeamEmailForm(request.POST if 'apply' in request.POST else None)

        if form.is_bound and form.is_valid():
            self._send_team_emails(request, teams, form.cleaned_data)
            return None

        context = {
            **self.admin_site.each_context(request),
            'title': 'Poslať email vybraným tímom',
            'opts': self.model._meta,
            'form': form,
            'recipients': self._plan_recipients(teams),
            'queryset': queryset,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'action_name': 'send_email',
        }
        return TemplateResponse(
            request, 'admin/kos/team/send_email.html', context)

    @staticmethod
    def _plan_recipients(teams):
        """Vráti zoznam (tím, adresa, tím s rovnakou adresou ktorému už email ide).
        Na každú adresu (bez ohľadu na veľkosť písmen) sa pošle iba jeden email."""
        first_team_by_address = {}
        rows = []
        for team in teams:
            address = (team.contact_email or '').strip() or None
            duplicate_of = None
            if address:
                key = address.lower()
                duplicate_of = first_team_by_address.setdefault(key, team)
                if duplicate_of is team:
                    duplicate_of = None
            rows.append((team, address, duplicate_of))
        return rows

    def _send_team_emails(self, request, teams, data):
        sent = 0
        failed = []
        no_email = []
        duplicates = []
        connection = get_connection()
        text_body = html_to_text(data['body'])
        html_body = wrap_html(data['body'])
        for team, address, duplicate_of in self._plan_recipients(teams):
            if not address:
                no_email.append(team.name)
                continue
            if duplicate_of is not None:
                duplicates.append(f'{team.name} (= {duplicate_of.name})')
                continue
            year = team.game.year
            reply_to = [year.contact_email] if year is not None and year.contact_email else None
            message = EmailMultiAlternatives(
                subject=data['subject'],
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[address],
                reply_to=reply_to,
                connection=connection,
            )
            message.attach_alternative(html_body, 'text/html')
            try:
                message.send()
                sent += 1
            except Exception:  # pylint: disable=broad-except
                failed.append(f'{team.name} ({address})')

        self.message_user(request, f'Odoslané emaily: {sent}', messages.SUCCESS)
        if no_email:
            self.message_user(
                request, 'Tímy bez emailovej adresy: ' + ', '.join(no_email),
                messages.WARNING)
        if duplicates:
            self.message_user(
                request, 'Rovnaká adresa ako iný tím, email poslaný iba raz: '
                + ', '.join(duplicates), messages.INFO)
        if failed:
            self.message_user(
                request, 'Nepodarilo sa odoslať: ' + ', '.join(failed),
                messages.ERROR)


@admin.register(models.Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'location')
    list_filter = ('game',)


@admin.register(models.Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'is_active', 'is_public',
                    'contact_email')


@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'year')
    list_filter = ('year',)

    actions = ["freeze_results", "delete_users"]

    @admin.action(description="Zmraz výsledky")
    def freeze_results(self, request, queryset):
        """Zmrazit výsledky"""
        for game in queryset.all():
            game.frozen_results_json = json.dumps(
                game.generate_results(), default=str)
            game.save()

    @admin.action(description="Zmaž používateľov tímov",
                  permissions=['delete'])
    def delete_users(self, request, queryset):
        """Zmaže používateľov všetkých tímov vo vybraných šifrovačkách"""
        return delete_team_users(
            self, request, queryset,
            models.Team.objects.filter(game__in=queryset))


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('submitted_at', 'competitor_answer')


@admin.register(models.PuzzleTeamState)
class TeamPuzzleStateAdmin(admin.ModelAdmin):
    list_display = ('puzzle', 'team', 'skipped',
                    'solved', 'started_at', 'ended_at')


@admin.register(models.Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ('puzzle', 'show_after',
                    'hint_penalty', 'count_as_penalty', 'is_dead', 'get_game')
    list_filter = ('count_as_penalty', 'puzzle')

    @admin.display(ordering='puzzle__game', description='Šifrovačka')
    def get_game(self, obj):
        return obj.puzzle.game
