"""Admin for Kos app"""
from django.contrib import admin

from kos import models

#pylint: disable=missing-docstring


class TeamMemberInline(admin.TabularInline):
    model = models.TeamMember


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'is_online')
    list_filter = ('game', 'is_online')
    inlines = [TeamMemberInline]


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


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('team', 'puzzle', 'submitted_at', 'competitor_answer')
    list_filter = ('team', 'puzzle')


@admin.register(models.Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ('puzzle', 'show_after', 'hint_penalty', 'count_as_penalty')
    list_filter = ('count_as_penalty', 'puzzle')
