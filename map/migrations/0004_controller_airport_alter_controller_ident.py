# Generated by Django 5.0.2 on 2024-03-03 23:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0003_remove_controller_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='controller',
            name='airport',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='map.airport'),
        ),
        migrations.AlterField(
            model_name='controller',
            name='ident',
            field=models.CharField(max_length=4),
        ),
    ]
