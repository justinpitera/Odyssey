# Generated by Django 5.0.2 on 2024-03-11 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0012_vatsimflight'),
    ]

    operations = [
        migrations.AddField(
            model_name='vatsimflight',
            name='departure_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
