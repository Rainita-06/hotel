from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hotel_app", "0004_userprofile_role_dynamic"),
    ]

    operations = [
        migrations.CreateModel(
            name="TwilioSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "account_sid",
                    models.CharField(blank=True, default="", max_length=64),
                ),
                (
                    "auth_token",
                    models.CharField(blank=True, default="", max_length=128),
                ),
                (
                    "whatsapp_from",
                    models.CharField(blank=True, default="", max_length=34),
                ),
                (
                    "test_to_number",
                    models.CharField(blank=True, default="", max_length=34),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="twilio_settings_updates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Twilio Setting",
                "verbose_name_plural": "Twilio Settings",
                "db_table": "twilio_settings",
            },
        ),
    ]

