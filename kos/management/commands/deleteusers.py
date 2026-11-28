from django.core.management.base import BaseCommand

from kos.models import Team


class Command(BaseCommand):
    help = 'Delete all users related to teams in competition'

    def add_arguments(self, parser):
        parser.add_argument('game_id', type=int)

    def handle(self, *args, **options):
        game_id: int = options['game_id']
        teams = Team.objects.filter(game=game_id).select_related('user')
        for team in teams:
            user = team.user
            if user is None:
                self.stdout.write(f'Team {team} already has no user')
                continue
            if team.delete_user():
                self.stdout.write(f'Deleted user {user}')
            else:
                self.stdout.write(f'Skipping staff user {user} of team {team}')
