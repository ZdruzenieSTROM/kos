from django.db import migrations, models
from django.db.models import Count, Min


def merge_duplicate_states(apps, schema_editor):
    """Zlúči duplicitné stavy tímu na šifre (issue #148).

    Ponechá stav s najnižším id, prenesie naň odovzdania a zlúči príznaky
    a časy z duplikátov. Ostatné duplikáty zmaže.
    """
    PuzzleTeamState = apps.get_model('kos', 'PuzzleTeamState')
    Submission = apps.get_model('kos', 'Submission')

    duplicates = (
        PuzzleTeamState.objects
        .values('team_id', 'puzzle_id')
        .annotate(count=Count('id'), keep_id=Min('id'))
        .filter(count__gt=1)
    )
    for group in duplicates:
        states = list(
            PuzzleTeamState.objects
            .filter(team_id=group['team_id'], puzzle_id=group['puzzle_id'])
            .order_by('id')
        )
        keep, others = states[0], states[1:]
        for other in others:
            keep.solved = keep.solved or other.solved
            keep.skipped = keep.skipped or other.skipped
            if other.started_at is not None and (
                    keep.started_at is None or other.started_at < keep.started_at):
                keep.started_at = other.started_at
            if other.ended_at is not None and (
                    keep.ended_at is None or other.ended_at < keep.ended_at):
                keep.ended_at = other.ended_at
        Submission.objects.filter(
            puzzle_team_state__in=others).update(puzzle_team_state=keep)
        keep.save()
        PuzzleTeamState.objects.filter(pk__in=[o.pk for o in others]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0035_alter_puzzleteamstate_started_at_and_more'),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_states, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='puzzleteamstate',
            constraint=models.UniqueConstraint(
                fields=('team', 'puzzle'), name='unique_puzzle_team_state'),
        ),
    ]
