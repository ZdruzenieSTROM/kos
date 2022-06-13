"""Admin for Kos app"""
from django.contrib import admin

from kos import models

#pylint: disable=missing-docstring


class TeamMemberInline(admin.TabularInline):
    model = models.TeamMember


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'is_online', 'category')
    list_filter = ('game', 'is_online', 'category')
    inlines = [TeamMemberInline]


@admin.register(models.Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'location')
    list_filter = ('game',)


@admin.register(models.Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end')


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'slug')
    list_filter = ('is_active',)


@admin.register(models.Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('team', 'puzzle', 'submited_at', 'competitor_answer')
    list_filter = ('team', 'puzzle')
