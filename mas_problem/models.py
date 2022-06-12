from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields import BooleanField

# Create your models here.

User = get_user_model()  # Neviem ci bude stacit django USer model pr9padne si ho uprav


class Grade(models.Model):
    verbose_name = models.CharField(max_length=50)
    shortcut = models.CharField(max_length=5)


class Game(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    max_session_duration = models.DurationField()


class Level(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    order = models.IntegerField()
    min_solved_to_unlock = models.IntegerField()
    is_starting_level_for_grades = models.ManyToManyField(Grade, blank=True)
    previous_level = models.ForeignKey(
        'Level', on_delete=models.SET_NULL, null=True, blank=True)


class Competitor(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # Nechajme zatial ako text, časom prepojíme asi v backendom stránky
    school = models.CharField(max_length=128)
    grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    current_level = models.ForeignKey(
        Level, on_delete=models.CASCADE, null=True)
    is_active = BooleanField()


class Problem(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    text = models.TextField()
    solution = models.FloatField()  # Treba overiť čo všetko môže byť výsledok


class Submission(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    competitor = models.ForeignKey(Competitor, on_delete=models.CASCADE)
    competitor_answer = models.FloatField()  # Upravit podla Problem.solution
    submited_at = models.DateTimeField()
    correct = models.BooleanField()  # Neviem ci bude nutné nechám na zváženie
