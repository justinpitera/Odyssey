# Generated by Django 5.0.1 on 2024-02-24 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='current_altitude',
            field=models.IntegerField(null=True),
        ),
    ]