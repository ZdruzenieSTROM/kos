# Generated by Django 4.0 on 2022-08-29 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0018_game_year'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='year',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='games', to='kos.year', verbose_name='Ročník'),
        ),
    ]
