# Generated by Django 4.0 on 2023-09-04 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0032_merge_20230904_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='hint',
            name='is_dead',
            field=models.BooleanField(default=False, verbose_name='Hint je riešenie'),
        ),
    ]