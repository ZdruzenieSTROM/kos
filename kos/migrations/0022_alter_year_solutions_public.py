# Generated by Django 4.0 on 2022-09-06 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0021_year_solutions_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='year',
            name='solutions_public',
            field=models.BooleanField(default=False, verbose_name='Zverejnené riešenia'),
        ),
    ]
