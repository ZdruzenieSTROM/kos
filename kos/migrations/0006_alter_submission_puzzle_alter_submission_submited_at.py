# Generated by Django 4.0 on 2022-08-04 19:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kos', '0005_puzzle_unlock_code_alter_puzzle_solution'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='puzzle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='kos.puzzle'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submited_at',
            field=models.DateTimeField(auto_created=True, auto_now=True),
        ),
    ]