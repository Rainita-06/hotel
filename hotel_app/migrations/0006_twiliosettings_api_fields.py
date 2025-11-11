from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hotel_app", "0005_twiliosettings"),
    ]

    operations = [
        migrations.AddField(
            model_name="twiliosettings",
            name="api_key_secret",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="twiliosettings",
            name="api_key_sid",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]

