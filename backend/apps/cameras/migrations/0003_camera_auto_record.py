from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cameras", "0002_visioncapture"),
    ]

    operations = [
        migrations.AddField(
            model_name="camera",
            name="auto_record",
            field=models.BooleanField(default=True),
        ),
    ]
