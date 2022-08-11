# Generated by Django 4.0 on 2022-08-11 21:30

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0011_game_is_public'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='submited_at',
            new_name='submitted_at',
        ),
        migrations.AlterField(
            model_name='hint',
            name='hint_penalty',
            field=models.DurationField(default=datetime.timedelta(0), verbose_name='Penalta za predošlé hinty'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='kos.team'),
        ),
    ]
