# Generated by Django 5.0.1 on 2024-02-23 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='rank',
            field=models.CharField(default='Cadet', max_length=100),
        ),
    ]
