# Generated by Django 3.2.10 on 2022-01-03 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="coursedate",
            options={"ordering": ["start", "pk"]},
        ),
        migrations.AddField(
            model_name="coursetype",
            name="fitness_level",
            field=models.TextField(blank=True),
        ),
    ]