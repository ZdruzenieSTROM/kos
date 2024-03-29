# Generated by Django 4.0 on 2022-08-09 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0007_remove_puzzle_offline_show_delay_hint_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hint',
            name='prerequisites',
            field=models.ManyToManyField(null=True, to='kos.Hint', verbose_name='Nutné zobrať pred'),
        ),
        migrations.AlterField(
            model_name='team',
            name='hints_taken',
            field=models.ManyToManyField(null=True, to='kos.Hint', verbose_name='Zobraté hinty'),
        ),
    ]
