# Generated by Django 5.0.2 on 2024-02-23 04:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Airline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('iata_code', models.CharField(blank=True, max_length=2, null=True, unique=True)),
                ('icao_code', models.CharField(blank=True, max_length=3, null=True, unique=True)),
                ('country', models.CharField(max_length=255)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='airline_logos/')),
            ],
        ),
    ]