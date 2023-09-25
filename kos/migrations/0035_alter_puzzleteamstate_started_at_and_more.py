# Generated by Django 4.0 on 2023-09-20 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0034_alter_puzzleteamstate_started_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='puzzleteamstate',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Začiatok riešenia'),
        ),
        migrations.AlterField(
            model_name='team',
            name='is_online',
            field=models.BooleanField(default=False, verbose_name='Je tím online'),
        ),
    ]