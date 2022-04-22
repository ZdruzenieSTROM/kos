from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Competitor, Grade, Game, Level, Problem, Submission

admin.site.register(Competitor)
admin.site.register(Grade)
admin.site.register(Game)
admin.site.register(Level)
admin.site.register(Problem)
admin.site.register(Submission)
