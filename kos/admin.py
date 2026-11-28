"""Admin for Kos app"""
import json

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from kos import models

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


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'is_online', 'paid')
    list_filter = ('game', 'is_online', 'paid')
    inlines = [TeamMemberInline]

    actions = ['delete_users']

    @admin.action(description='Zmaž používateľov vybraných tímov',
                  permissions=['delete'])
    def delete_users(self, request, queryset):
        """Zmaže používateľov vybraných tímov"""
        return delete_team_users(self, request, queryset, queryset)


@admin.register(models.Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'location')
    list_filter = ('game',)


@admin.register(models.Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'is_active', 'is_public')


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
