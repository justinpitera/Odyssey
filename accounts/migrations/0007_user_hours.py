# Generated by Django 5.0.1 on 2024-02-23 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_user_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hours',
            field=models.IntegerField(default=0),
        ),
    ]
