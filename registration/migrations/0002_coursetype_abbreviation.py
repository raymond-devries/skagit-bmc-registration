# Generated by Django 3.1.3 on 2020-12-28 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="coursetype",
            name="abbreviation",
            field=models.CharField(default="RC1", max_length=5),
            preserve_default=False,
        ),
    ]
