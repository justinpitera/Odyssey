# Generated by Django 5.0.1 on 2024-02-24 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Flight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flight_number', models.CharField(max_length=10)),
                ('departure', models.CharField(max_length=100)),
                ('destination', models.CharField(max_length=100)),
                ('departure_time', models.DateTimeField()),
                ('arrival_time', models.DateTimeField()),
                ('aircraft', models.CharField(max_length=100)),
                ('capacity', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('available_seats', models.IntegerField()),
            ],
        ),
    ]