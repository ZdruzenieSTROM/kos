# Generated by Django 4.0 on 2022-09-11 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0023_merge_20220906_2236'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='after_game_message',
            field=models.TextField(blank=True, null=True, verbose_name='Správa po ukončení hry'),
        ),
        migrations.AddField(
            model_name='game',
            name='before_game_message',
            field=models.TextField(blank=True, null=True, verbose_name='Správa pred začatím hry'),
        ),
        migrations.AlterField(
            model_name='game',
            name='final_message',
            field=models.TextField(blank=True, null=True, verbose_name='Správa po vyriešení všetkých šifier'),
        ),
    ]