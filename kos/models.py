
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Max, Q
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
    photo_url = models.TextField(
        verbose_name='Link na fotogalériu', null=True, blank=True)
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
        verbose_name='Serializované výsledky', null=True, blank=True)

    def __str__(self):
        return f'{self.year.name} - {self.name}'

    def add_places(self, results):
        current_place = 1
        previous_last_correct_submission = None
        previous_solved = None
        results_list = []
        for i, result_row in enumerate(results):
            if previous_last_correct_submission != result_row.last_correct_submission \
                    or previous_solved != result_row.solved_puzzles:
                current_place = i+1
                previous_last_correct_submission = result_row.last_correct_submission
                previous_solved = result_row.solved_puzzles
            result_row.place = current_place
            results_list.append(
                {
                    'place': current_place,
                    'name': result_row.name,
                    'members_joined': result_row.members_joined(),
                    'solved_puzzles': result_row.solved_puzzles,
                    'last_correct_submission': result_row.last_correct_submission

                }
            )
        return results_list

    def generate_results(self):
        game_results = {}
        public_condition = Q(is_public=True)
        email_verified_condition = Q(user__emailaddress__verified=True)
        # We want to also display teams with no email address or no user, for example if we delete the users manually
        no_email_condition = Q(user__emailaddress=None)
        results = self.team_set.filter(public_condition & (email_verified_condition | no_email_condition)).annotate(
            last_correct_submission=Max(
                'states__ended_at', filter=Q(states__solved=True)),
            solved_puzzles=Count('states', filter=Q(states__solved=True)),
        ).order_by('-solved_puzzles', 'last_correct_submission')
        game_results['online_teams'] = self.add_places(
            results.filter(is_online=True))
        game_results['offline_teams'] = self.add_places(
            results.filter(is_online=False))
        game_results['name'] = str(self)
        return game_results


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
    skip_allowed_after = models.DurationField(
        verbose_name='Skip', help_text='Čas po ktorom je možné preskočiť šifru')

    def __str__(self):
        return self.name

    def team_submissions(self, team):
        """Vráti pokusy o odovzdanie pre daný tím"""
        return PuzzleTeamState.objects.get(team=team, puzzle=self).submissions

    def has_team_passed(self, team):
        """Vráti bool či tím už šifru vyriešil"""
        state = PuzzleTeamState.objects.get(team=team, puzzle=self)
        return state is not None and not state.is_open

    @staticmethod
    def clean_text(string: str):
        """Normalizuje text pre správne porovnanie.
        Odstráni diakritiku, krajné medzery a prevedie na malé písmená"""
        return unidecode(string).lower().strip()

    def team_timeout(self, team):
        """Vráti čas, o ktorý bude daný tím môcť znova odovzdať túto úlohu"""
        submissions = self.team_submissions(team).filter(
            correct=False, is_submitted_as_unlock_code=False)
        if submissions.count() < 3:
            return timedelta(0)
        time_of_last_submission = submissions.order_by(
            '-submitted_at')[0].submitted_at
        return time_of_last_submission + timedelta(seconds=60) - now()

    def can_team_submit(self, team):
        return team.current_level >= self.level and not self.team_timeout(team) > timedelta(0) and not self.has_team_passed(team)

    def can_team_skip(self, team):
        started_at = PuzzleTeamState.objects.get(
            team=team, puzzle=self).started_at
        if started_at is None:
            return False
        return team.current_level >= self.level and not self.has_team_passed(team) and \
            started_at + self.skip_allowed_after <= now()

    def team_skip_time(self, team):
        # TODO: use team.current_puzzle_start_time()
        started_at = PuzzleTeamState.objects.get(
            team=team, puzzle=self).started_at
        if started_at is None:
            return None
        # TODO: temporary solution for 2023 testing, 15 should be stored on the puzzle
        return started_at + self.skip_allowed_after + timedelta(minutes=15) * team.get_penalties(self.level)

    @staticmethod
    def __check_equal(string1: str, string2: str) -> bool:
        return Puzzle.clean_text(string1) == Puzzle.clean_text(string2)

    def check_solution(self, team_solution: str) -> bool:
        """Skontroluje riešenie"""

        return any(
            self.__check_equal(team_solution, solution)
            for solution in self.solution.split(settings.SOLUTION_DELIMITER))

    def check_unlock(self, team_submission: str) -> bool:
        """Skontroluje odomykací kód na mieste"""
        return self.__check_equal(team_submission, self.unlock_code)

    def can_team_see(self, team):
        """Skontroluje, či tím môže vidieť zadanie šifry"""
        return team.is_online or self.team_submissions(team).filter(
            is_submitted_as_unlock_code=True,
            correct=True
        ).exists()  # TODO: this logic should probably be moved to PuzzleTeamState

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
        """Vráti najskorší čas, kedy sa tímu odomkne hint, odovzdávanie alebo skip
        Vráti None ak tím na nič nečaká"""
        earliest_hint_timeout = self.earliest_hint_timeout(team)
        submission_timeout = self.team_timeout(team)
        skip_time = self.team_skip_time(team)

        relevant_timeouts = []
        if earliest_hint_timeout is not None:
            relevant_timeouts.append(earliest_hint_timeout)
        if submission_timeout > timedelta(0):
            relevant_timeouts.append(submission_timeout)
        if skip_time is not None:
            skip_timeout = skip_time - now()
            if skip_timeout > timedelta(0):
                relevant_timeouts.append(skip_timeout)

        if not relevant_timeouts:
            return None
        return min(relevant_timeouts)


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
    is_dead = models.BooleanField(
        verbose_name='Hint je riešenie', default=False)
    prerequisites = models.ManyToManyField(
        'Hint', verbose_name='Nutné zobrať pred', blank=True)

    def __str__(self):
        return f'{self.puzzle} - {self.text[:30]}'

    def get_time_to_take(self, team):
        """Zostávajúci čas do hintu"""
        elapsed_time = now() - team.current_puzzle_start_time()
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
            and not self.puzzle.has_team_passed(team)
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
    is_online = models.BooleanField(
        verbose_name='Je tím online', default=False)
    hints_taken = models.ManyToManyField(
        Hint, verbose_name='Zobraté hinty', blank=True)
    paid = models.BooleanField(verbose_name='Poplatok uhradený', default=False)
    is_public = models.BooleanField(
        verbose_name='Tím je verejný', default=True)

    @property
    def editable(self) -> bool:
        """
        Vráti, či je ešte možné robiť zmeny v tíme.
        Aktuálne tímom dovoľujeme meniť meno a členov tímu
        do konca šifrovačky. Zákaz menenia toho, či je tím
        online je implementovaný inde."""
        return self.game.year.end > now()

    def __str__(self):
        return f'{self.name}'

    def get_penalties(self, on_level) -> int:
        """Spočíta počet zobratých hintov, ktoré sa rátajú ako penalty"""
        return self.hints_taken.filter(count_as_penalty=True, puzzle__level__lt=on_level).count()

    def current_puzzle_state(self):
        try:
            current_puzzle = self.game.puzzle_set.get(level=self.current_level)
        except Puzzle.DoesNotExist:
            return None
        return self.states.get(team=self, puzzle=current_puzzle)

    def current_puzzle_start_time(self):
        """Vráti čas začiatku riešenia aktuálnej šifry alebo začiatok hry ak tím ešte nezačal riešiť žiadnu šifru"""
        state = self.current_puzzle_state()
        if not state or not state.started_at:
            return self.game.year.start
        return state.started_at

    def pass_level(self, level: int):
        self.current_level = max(level + 1, self.current_level)
        self.save()

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


class PuzzleTeamState(models.Model):
    class Meta:
        verbose_name = 'Stav tímu na šifre'
        verbose_name_plural = 'Stavy tímov na šifrách'
    puzzle = models.ForeignKey(
        Puzzle, on_delete=models.CASCADE, related_name='states')
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='states')
    skipped = models.BooleanField(
        verbose_name='Tím preskočil šifru', default=False)
    solved = models.BooleanField(
        verbose_name='Tím vyriešil šifru', default=False)
    started_at = models.DateTimeField(
        verbose_name='Začiatok riešenia', null=True, blank=True)
    ended_at = models.DateTimeField(
        verbose_name='Koniec riešenia', null=True, blank=True, default=None)

    @property
    def is_open(self):
        return not self.solved and not self.skipped

    @property
    def is_unlocked(self):
        return self.started_at is not None

    @classmethod
    def get_or_create(cls, team: Team, puzzle: Puzzle):
        if team.is_online:
            start = now() if puzzle.level > 1 else puzzle.game.year.start
        else:
            start = None
        state, _ = PuzzleTeamState.objects.get_or_create(
            team=team,
            puzzle=puzzle,
            defaults={'started_at': start}
        )
        return state

    def skip_puzzle(self):
        self.skipped = True
        self.ended_at = now()
        self.team.pass_level(self.puzzle.level)
        game_logger = logging.getLogger('game')
        game_logger.info('Team %s: skipped puzzle %s', self.team, self.puzzle)
        self.save()

    def solve_puzzle(self):
        self.solved = True
        self.ended_at = now()
        self.team.pass_level(self.puzzle.level)
        game_logger = logging.getLogger('game')
        game_logger.info('Team %s: solved puzzle %s', self.team, self.puzzle)
        self.save()

    def submit_unlock_code(self, unlock_code: str):
        game_logger = logging.getLogger('game')
        is_correct = self.puzzle.check_unlock(unlock_code)
        Submission.objects.create(
            puzzle_team_state=self,
            competitor_answer=Puzzle.clean_text(unlock_code),
            correct=is_correct,
            is_submitted_as_unlock_code=True
        )
        game_logger.info('Team %s: submitted unlock code %s on puzzle %s',
                         self.team, unlock_code.upper(), self.puzzle)
        if is_correct and self.started_at is None:
            self.started_at = now()
            game_logger.info('Team %s: unlocked %s', self.team, self.puzzle)
            self.save()

    def submit_solution(self, team_solution: str):
        is_correct = self.puzzle.check_solution(team_solution)
        Submission.objects.create(
            puzzle_team_state=self,
            competitor_answer=Puzzle.clean_text(team_solution),
            correct=is_correct,
            is_submitted_as_unlock_code=False
        )
        game_logger = logging.getLogger('game')
        game_logger.info('Team %s: submitted solution %s on puzzle %s',
                         self.team, team_solution.upper(), self.puzzle)
        if is_correct:
            self.solve_puzzle()


class Submission(models.Model):
    """Pokus o odovzdanie odpovede na šifru"""

    class Meta:
        verbose_name = 'odovzdanie šifry'
        verbose_name_plural = 'odovzdania šifier'
    puzzle_team_state = models.ForeignKey(
        PuzzleTeamState, on_delete=models.SET_NULL, null=True, related_name='submissions')
    competitor_answer = models.CharField(max_length=100)
    submitted_at = models.DateTimeField(auto_now=True, auto_created=True)
    correct = models.BooleanField()  # Neviem ci bude nutné nechám na zváženie
    is_submitted_as_unlock_code = models.BooleanField(
        verbose_name='Pokus odovzdaný ako vstupný kód', default=False)
