# Generated by Django 5.1.2 on 2025-02-26 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='startdate',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
