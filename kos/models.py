

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Max
from django.utils.timezone import now
from unidecode import unidecode

User = get_user_model()


class Year(models.Model):
    """Ročník šiforvačky"""

    class Meta:
        verbose_name = 'Ročník'
        verbose_name_plural = 'Ročníky'

    name = models.CharField(max_length=100)
    start = models.DateTimeField(verbose_name='Začiatok hry')
    end = models.DateTimeField(verbose_name='Koniec hry')
    is_public = models.BooleanField(verbose_name='Verejná hra', default=True)
    is_active = models.BooleanField(
        verbose_name='Hra je aktívna', default=False
    )

    def __str__(self):
        return self.name


class Game(models.Model):
    """Šifrovacia hra/ ročník šifrovačky"""
    class Meta:
        verbose_name = 'šifrovačka'
        verbose_name_plural = 'šifrovačky'

    name = models.CharField(max_length=100)
    year = models.ForeignKey(
        Year, on_delete=models.SET_NULL, null=True, verbose_name='Ročník', related_name='games')

    def __str__(self):
        return f'{self.year.name} - {self.name}'


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
    pdf_solution = models.FileField(
        verbose_name='Riešenie v PDF', null=True, blank=True)
    level = models.PositiveIntegerField(verbose_name='Úroveň/Poradie')
    location = models.TextField(null=True)

    def __str__(self):
        return self.name

    def team_submissions(self, team):
        """Vráti pokusy o odovzdanie pre daný tím"""
        return self.submissions.filter(team=team)

    def has_team_passed(self, team):
        """Vráti bool či tím už šifru vyriešil"""
        return self.submissions.filter(team=team).aggregate(Max('correct'))['correct__max']

    def team_timeout(self, team):
        """Vráti čas, o ktorý bude daný tím môcť znova odovzdať túto úlohu"""
        submission = self.team_submissions(team)
        if submission.count() < 3:
            return timedelta()
        time_of_last_submission = submission.order_by(
            '-submitted_at')[0].submitted_at
        return time_of_last_submission + timedelta(seconds=60) - now()

    def can_team_submit(self, team):
        return team.current_level >= self.level and not self.team_timeout(team) > timedelta()

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
        verbose_name='Penalta za predošlé hinty', default=timedelta(0))
    count_as_penalty = models.BooleanField(
        verbose_name='Počíta sa do penalty')
    prerequisites = models.ManyToManyField(
        'Hint', verbose_name='Nutné zobrať pred', blank=True)

    def get_time_to_take(self, team):
        """Zostávajúci čas do hintu"""
        last_submission = team.get_last_correct_submission_time()
        if last_submission is None:
            last_submission = self.puzzle.game.year.start
        elapsed_time = now() - last_submission
        minimum_elapsed_time = self.show_after + self.hint_penalty*team.get_penalties()
        return minimum_elapsed_time - elapsed_time

    def time_when_will_be_unlocked(self, team):
        """Čas, kedy si daný tým bude môcť zobrať tento hint"""
        time_to_take = self.get_time_to_take(team)
        return now() + time_to_take

    def all_prerequisites_met(self, team):
        return set(team.hints_taken.all()).issuperset(set(self.prerequisites.all()))

    def can_team_take(self, team):
        time_to_take = self.get_time_to_take(team)
        return (
            self.all_prerequisites_met(team)
            and not time_to_take > timedelta()
            and not team.hints_taken.filter(pk=self.pk).exists()
            and not team.submissions.filter(correct=True, puzzle=self.puzzle).exists()
        )


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
    hints_taken = models.ManyToManyField(
        Hint, verbose_name='Zobraté hinty', blank=True)

    def __str__(self):
        return f'{self.name}'

    def get_penalties(self) -> int:
        """Spočíta počet zobratých hintov, ktoré sa rátajú ako penalty"""
        return self.hints_taken.filter(count_as_penalty=True).count()

    def get_last_correct_submission_time(self):
        """Vráti čas poslednej správne odovzdanej šifry"""
        return self.submissions.filter(correct=True).aggregate(
            Max('submitted_at')
        )['submitted_at__max']

    def members_joined(self):
        return ','.join([member.name for member in self.members.all()])


class TeamMember(models.Model):
    """Člen tímu"""
    class Meta:
        verbose_name = 'Člen tímu'
        verbose_name_plural = 'Členovia tímov'
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='members')
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
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='submissions')
    competitor_answer = models.CharField(max_length=100)
    submitted_at = models.DateTimeField(auto_now=True, auto_created=True)
    correct = models.BooleanField()  # Neviem ci bude nutné nechám na zváženie
