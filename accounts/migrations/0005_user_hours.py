# Generated by Django 5.0.1 on 2024-02-23 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hours',
            field=models.IntegerField(default=0),
        ),
    ]
