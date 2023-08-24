

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
    solutions_public = models.BooleanField(
        verbose_name='Zverejnené riešenia', default=False)
    is_active = models.BooleanField(
        verbose_name='Hra je aktívna', default=False
    )
    registration_deadline = models.DateTimeField(verbose_name='Registrácia do')

    def __str__(self):
        return self.name


class Game(models.Model):
    """Šifrovacia hra/ ročník šifrovačky"""
    class Meta:
        verbose_name = 'šifrovačka'
        verbose_name_plural = 'šifrovačky'
    final_message = models.TextField(
        blank=True, null=True, verbose_name='Správa po vyriešení všetkých šifier')
    before_game_message = models.TextField(
        blank=True, null=True, verbose_name='Správa pred začatím hry')
    after_game_message = models.TextField(
        blank=True, null=True, verbose_name='Správa po ukončení hry')
    name = models.CharField(max_length=100)
    year = models.ForeignKey(
        Year, on_delete=models.SET_NULL, null=True, verbose_name='Ročník', related_name='games')
    price_offline = models.DecimalField(
        verbose_name='Výška poplatku terénnej verzie', max_digits=5, decimal_places=2, default=0.0)
    price_online = models.DecimalField(
        verbose_name='Výška poplatku online verzie', max_digits=5, decimal_places=2, default=0.0)
    frozen_results_json = models.TextField(
        verbose_name='Serializované výsledky')

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
        return self.submissions.filter(team=team, is_submitted_as_unlock_code=False).aggregate(Max('correct'))['correct__max']

    @staticmethod
    def clean_text(string: str):
        """Normalizuje text pre správne porovnanie.
        Odstráni diakritiku, krajné medzery a prevedie na malé písmená"""
        return unidecode(string).lower().strip()

    def team_timeout(self, team):
        """Vráti čas, o ktorý bude daný tím môcť znova odovzdať túto úlohu"""
        submission = self.team_submissions(team).filter(
            correct=False, is_submitted_as_unlock_code=False)
        if submission.count() < 3:
            return timedelta(0)
        time_of_last_submission = submission.order_by(
            '-submitted_at')[0].submitted_at
        return time_of_last_submission + timedelta(seconds=60) - now()

    def can_team_submit(self, team):
        return team.current_level >= self.level and not self.team_timeout(team) > timedelta(0) and not self.has_team_passed(team)

    @staticmethod
    def __check_equal(string1: str, string2: str) -> bool:
        return Puzzle.clean_text(string1) == Puzzle.clean_text(string2)

    def check_solution(self, team_solution: str) -> bool:
        """Skontroluje riešenie"""
        return self.__check_equal(team_solution, self.solution)

    def check_unlock(self, team_submission: str) -> bool:
        """Skontroluje odomykací kód na mieste"""
        return self.__check_equal(team_submission, self.unlock_code)

    def can_team_see(self, team):
        """Skontroluje, či tím môže vidieť zadanie šifry"""
        return team.is_online or self.submissions.filter(
            team=team,
            is_submitted_as_unlock_code=True,
            correct=True
        ).exists()

    def earliest_hint_timeout(self, team):
        """Vráti najskorší čas, kedy sa tímu odomkne nejaký hint
        Vráti None ak tím na žiaden hint nečaká"""
        earliest_hint_timeout = None
        for hint in self.hint_set.all():
            hint_timeout = hint.get_time_to_take(team)
            if hint_timeout > timedelta(0) and (earliest_hint_timeout is None or hint_timeout < earliest_hint_timeout):
                earliest_hint_timeout = hint_timeout
        return earliest_hint_timeout

    def earliest_timeout(self, team):
        """Vráti najskorší čas, kedy sa tímu odomkne hint alebo odovzdávanie
        Vráti None ak tím na nič nečaká"""
        earliest_hint_timeout = self.earliest_hint_timeout(team)
        submission_timeout = self.team_timeout(team)
        if earliest_hint_timeout is None:
            if submission_timeout <= timedelta(0):
                return None
            return submission_timeout
        if submission_timeout <= timedelta(0):
            return earliest_hint_timeout
        return min(earliest_hint_timeout, submission_timeout)


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

    def __str__(self):
        return f'{self.puzzle} - {self.text[:30]}'

    def get_time_to_take(self, team):
        """Zostávajúci čas do hintu"""
        last_submission = team.get_last_correct_submission_time(
            answers_only=False)
        if last_submission is None:
            last_submission = self.puzzle.game.year.start
        elapsed_time = now() - last_submission
        minimum_elapsed_time = self.show_after + \
            self.hint_penalty*team.get_penalties(self.puzzle.level)
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
            and not time_to_take > timedelta(0)
            and not team.hints_taken.filter(pk=self.pk).exists()
            and not team.submissions.filter(
                correct=True,
                is_submitted_as_unlock_code=False,
                puzzle=self.puzzle
            ).exists()
            and self.puzzle.can_team_see(team)
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
        blank=True,
        primary_key=False,
        related_name='team'
    )
    email = models.EmailField(null=True, blank=True)
    current_level = models.PositiveSmallIntegerField(default=1)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    hints_taken = models.ManyToManyField(
        Hint, verbose_name='Zobraté hinty', blank=True)
    paid = models.BooleanField(verbose_name='Poplatok uhradený', default=False)

    def __str__(self):
        return f'{self.name}'

    def get_penalties(self, on_level) -> int:
        """Spočíta počet zobratých hintov, ktoré sa rátajú ako penalty"""
        return self.hints_taken.filter(count_as_penalty=True, puzzle__level__lt=on_level).count()

    def get_last_correct_submission_time(self, answers_only=True):
        """Vráti čas poslednej správne odovzdanej šifry"""
        submissions = self.submissions.filter(correct=True)
        if answers_only:
            submissions = submissions.filter(is_submitted_as_unlock_code=False)
        return submissions.aggregate(
            Max('submitted_at')
        )['submitted_at__max']

    def members_joined(self):
        return ', '.join([member.name for member in self.members.all()])


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
    is_submitted_as_unlock_code = models.BooleanField(
        verbose_name='Pokus odovzdaný ako vstupný kód', default=False)
