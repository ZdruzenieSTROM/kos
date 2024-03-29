# Generated by Django 4.0 on 2022-11-23 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0024_game_after_game_message_game_before_game_message_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='price_offline',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Výška poplatku terénnej verzie'),
        ),
        migrations.AddField(
            model_name='game',
            name='price_online',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Výška poplatku online verzie'),
        ),
        migrations.AddField(
            model_name='team',
            name='paid',
            field=models.BooleanField(default=False, verbose_name='Poplatok uhradený'),
        ),
    ]
