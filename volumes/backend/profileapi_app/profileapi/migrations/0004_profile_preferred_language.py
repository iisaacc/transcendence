# Generated by Django 4.2.16 on 2024-10-04 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profileapi', '0003_remove_profile_username_profile_display_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='preferred_language',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French'), ('es', 'Spanish')], default='en', max_length=2),
        ),
    ]
