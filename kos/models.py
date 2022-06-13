from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Game(models.Model):
    """Šifrovacia hra/ ročník šifrovačky"""
    class Meta:
        verbose_name = 'šifrovačka'
        verbose_name_plural = 'šifrovačky'

    name = models.CharField(max_length=100)
    start = models.DateTimeField(verbose_name='Začiatok hry')
    end = models.DateTimeField(verbose_name='Koniec hry')

    def __str__(self):
        return self.name


class Puzzle(models.Model):
    """Šifra"""
    class Meta:
        verbose_name = 'šifra'
        verbose_name_plural = 'šifry'

    name = models.CharField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True)
    solution = models.CharField(verbose_name='Riešenie', max_length=100)
    file = models.FileField(verbose_name='Zadanie')
    pdf_solution = models.FileField(verbose_name='Riešenie v PDF')
    level = models.PositiveIntegerField(verbose_name='Úroveň/Poradie')
    location = models.TextField(null=True)
    offline_show_delay = models.TimeField(null=True)

    def __str__(self):
        return self.name

    def team_submissions(self, team):
        pass

    def has_team_passed(self, team):
        """Vráti bool či tím už šifru vyriešil"""
        return False

    def check_solution(self, team_solution: str):
        # TODO: Maybe use unidecode
        return team_solution.lower() == self.solution.lower()


class Category(models.Model):
    """Kategória"""
    class Meta:
        verbose_name = 'kategória'
        verbose_name_plural = 'kategórie'
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField()

    def __str__(self):
        return self.name


class Team(models.Model):
    """Tím v hre"""

    class Meta:
        verbose_name = 'tím'
        verbose_name_plural = 'tímy'

    name = models.CharField(max_length=70)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    current_level = models.PositiveSmallIntegerField(default=1)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.name}'


class TeamMember(models.Model):
    """Člen tímu"""
    class Meta:
        verbose_name = 'Člen tímu'
        verbose_name_plural = 'Členovia tímov'
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.name} ({self.team})'


class Submission(models.Model):
    """Pokus o odovzdanie odpovede na šifru"""

    class Meta:
        verbose_name = 'odovzdanie šifry'
        verbose_name_plural = 'odovzdania šifier'
    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    competitor_answer = models.CharField(max_length=100)
    submited_at = models.DateTimeField()
    correct = models.BooleanField()  # Neviem ci bude nutné nechám na zváženie
