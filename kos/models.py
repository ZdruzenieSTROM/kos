

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Max
from unidecode import unidecode

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

    name = models.CharField(max_length=100, default='šifra')
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True)
    solution = models.CharField(verbose_name='Riešenie', max_length=50)
    unlock_code = models.CharField(
        verbose_name='Kód na odomknutie šifry', max_length=50, null=True)
    file = models.FileField(verbose_name='Zadanie')
    pdf_solution = models.FileField(verbose_name='Riešenie v PDF')
    level = models.PositiveIntegerField(verbose_name='Úroveň/Poradie')
    location = models.TextField(null=True)

    def __str__(self):
        return self.name

    def team_submissions(self, team):
        """Vráti pokusy o odovzdanie pre daný tím"""
        return self.submissions.filter(team=team)

    def has_team_passed(self, team):
        """Vráti bool či tím už šifru vyriešil"""
        return self.submissions.filter(team=team).aggregate(Max('correct'))

    @staticmethod
    def __check_equal(string1: str, string2: str) -> bool:
        return unidecode(string1).lower().strip() == unidecode(string2).lower().strip()

    def check_solution(self, team_solution: str) -> bool:
        """Skontroluje riešenie"""
        return self.__check_equal(team_solution, self.solution)

    def check_unlock(self, team_submission: str) -> bool:
        """Skontroluje odomykací kód na mieste"""
        return self.__check_equal(team_submission, self.unlock_code)


class Hint(models.Model):
    """Hint"""
    class Meta:
        verbose_name = 'hint'
        verbose_name_plural = 'hinty'

    puzzle = models.ForeignKey(Puzzle, on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Znenie hintu')
    show_after = models.DurationField(verbose_name='Povoliť zobrazenie po')
    hint_penalty = models.DurationField(
        verbose_name='Penalta za predošlé hinty', default=0)
    count_as_penalty = models.BooleanField(
        verbose_name='Počíta sa do penalty')
    prerequisites = models.ManyToManyField(
        'Hint', verbose_name='Nutné zobrať pred', blank=True)

    def get_time_to_take(self, team):
        """Zostávajúci čas do hintu"""
        if set(team.hints_taken).issuperset(set(self.prerequisites)):
            return None
        return self.show_after + self.hint_penalty*team.get_penalties()


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
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True,
        primary_key=False,
        related_name='team'
    )
    current_level = models.PositiveSmallIntegerField(default=1)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True)
    hints_taken = models.ManyToManyField(
        Hint, verbose_name='Zobraté hinty', blank=True)

    def __str__(self):
        return f'{self.name}'

    def get_penalties(self) -> int:
        """Spočíta počet zobratých hintov, ktoré sa rátajú ako penalty"""
        return self.hints_taken.filter(count_as_penalty=True).count()


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
    puzzle = models.ForeignKey(
        Puzzle, on_delete=models.CASCADE, related_name='submissions')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    competitor_answer = models.CharField(max_length=100)
    submited_at = models.DateTimeField(auto_now=True, auto_created=True)
    correct = models.BooleanField()  # Neviem ci bude nutné nechám na zváženie
