# Generated by Django 4.0 on 2022-08-09 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0009_alter_hint_prerequisites_alter_team_hints_taken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hint',
            name='hint_penalty',
            field=models.DurationField(default=0, verbose_name='Penalta za predošlé hinty'),
        ),
        migrations.AlterField(
            model_name='hint',
            name='show_after',
            field=models.DurationField(verbose_name='Povoliť zobrazenie po'),
        ),
    ]
