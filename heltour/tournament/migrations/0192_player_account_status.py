# Generated by Django 2.2.13 on 2021-10-08 05:40

from django.db import migrations, models


class Migration(migrations.Migration):
    
    def update_player_status(apps, schema_editor):
        # We can't import the Person model directly as it may be a newer
        # version than this migration expects. We use the historical version.
        Players = apps.get_model('tournament', 'Player')
        for player in Players.objects.all():
            if player.account_status in ('engine','booster'):
                player.account_status = 'tos_violation'
            player.save()

    dependencies = [
        ('tournament', '0191_auto_20210613_0346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='account_status',
            field=models.CharField(choices=[('normal', 'Normal'), ('tos_violation', 'ToS Violation'), ('closed', 'Closed')], default='normal', max_length=31),
        ),
        migrations.RunPython(update_player_status),
    ]
