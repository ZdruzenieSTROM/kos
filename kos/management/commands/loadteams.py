import csv
import random
import string

from django.core.management.base import BaseCommand
from kos.models import Game, Team, TeamMember, User


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str)

    def get_random_string(self, length):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

    def handle(self, *args, **options):
        with open(options['file'], newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            with open('processed.csv', 'w', newline='', encoding='utf-8') as csvoutput:
                writer = csv.DictWriter(
                    csvoutput, delimiter=';', fieldnames=reader.fieldnames)

                for row in reader:
                    password = self.get_random_string(
                        10) if row['password'] == '' else row['password']
                    user = User.objects.create_user(
                        row['email'], row['email'], password)
                    game_id = 0 if row['category'] == 'Začiatočníci' else 1
                    team = Team.objects.create(
                        user=user,
                        name=row['username'],
                        game=Game.objects.get(pk=game_id),
                        is_online=(row['is_online'] == 'Online'),
                        current_level=1
                    )

                    for i in range(1, 6):
                        if row[f'member_{i}'] != '':
                            TeamMember.objects.create(
                                team=team,
                                name=row[f'member_{i}']

                            )
                    out_row = row.copy()
                    out_row['password'] = password
                    writer.writerow(out_row)
