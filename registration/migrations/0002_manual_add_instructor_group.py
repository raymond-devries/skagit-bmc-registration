from django.db import migrations


def create_instructor_group(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    Group.objects.using(db_alias).get_or_create(name="instructor")


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_instructor_group),
    ]
