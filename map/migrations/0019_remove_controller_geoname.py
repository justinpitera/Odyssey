# Generated by Django 5.0.2 on 2024-03-14 01:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0018_controller_geoname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='controller',
            name='geoname',
        ),
    ]