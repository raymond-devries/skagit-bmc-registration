# Generated by Django 3.1.3 on 2021-01-01 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0006_auto_20210101_0133"),
    ]

    operations = [
        migrations.AddField(
            model_name="discount",
            name="stripe_id",
            field=models.CharField(default="96E10S1Y", max_length=50),
            preserve_default=False,
        ),
    ]