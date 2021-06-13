# Generated by Django 2.2.13 on 2021-06-13 03:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0190_auto_20210424_1519'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='player',
            options={'ordering': ['lichess_username'], 'permissions': (('change_player_details', 'Can change player details'), ('invite_to_slack', 'Can invite to slack'), ('link_slack', 'Can manually link slack accounts'), ('dox', 'Can see player emails'))},
        ),
    ]
