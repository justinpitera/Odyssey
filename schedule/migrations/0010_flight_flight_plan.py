# Generated by Django 5.0.2 on 2024-02-25 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0009_remove_flight_arrival_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='flight_plan',
            field=models.URLField(blank=True, null=True),
        ),
    ]
