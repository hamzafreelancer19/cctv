from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0002_person_sighting"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="watch_mobile_activity",
            field=models.BooleanField(
                default=False,
                help_text="Strict watch: log mobile use for this person on cameras",
            ),
        ),
    ]
