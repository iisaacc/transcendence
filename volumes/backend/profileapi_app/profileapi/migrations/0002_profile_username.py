# Generated by Django 4.2.16 on 2024-10-01 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profileapi', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='username',
            field=models.CharField(default='user', max_length=20),
        ),
    ]
