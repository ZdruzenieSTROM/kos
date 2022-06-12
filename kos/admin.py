
from django.contrib import admin

from kos import models


class TeamMemberInline(admin.TabularInline):
    model = models.TeamMember


class TeamAdmin(admin.ModelAdmin):
    model = models.Team
    inlines = [TeamMemberInline]


admin.site.register(models.Team)
admin.site.register(models.Puzzle)
admin.site.register(models.Game)
admin.site.register(models.Category)
admin.site.register(models.Submission)
