# Generated by Django 4.0 on 2023-09-01 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0029_remove_submission_correct_remove_submission_puzzle_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='puzzleteamstate',
            name='solved',
            field=models.BooleanField(default=False, verbose_name='Tím vyriešil šifru'),
        ),
    ]