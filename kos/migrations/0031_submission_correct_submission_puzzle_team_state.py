# Generated by Django 4.0 on 2023-09-01 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0030_alter_puzzleteamstate_solved'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='correct',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='puzzle_team_state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submissions', to='kos.puzzleteamstate'),
        ),
    ]
