# Generated by Django 4.0 on 2022-06-13 20:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('kos', '0003_alter_category_options_alter_game_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team', to='auth.user'),
        ),
    ]