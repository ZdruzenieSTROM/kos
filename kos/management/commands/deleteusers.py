
from django.core.management.base import BaseCommand

from kos.models import Team


class Command(BaseCommand):
    help = 'Delete all users related to teams in competition'

    def add_arguments(self, parser):
        parser.add_argument('game_id', type=int)

    def handle(self, *args, **options):
        game_id:int = options['game_id']
        teams = Team.objects.filter(game=game_id).all()
        for team in teams:
            team.email = team.user.email
            user = team.user
            print(f'Deleting user {user}')
            team.user = None
            user.delete()
            team.save()
        
