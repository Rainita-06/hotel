from django.db import migrations, models


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('hotel_app', 'UserProfile')
    mapping = {
        'admin': 'Admins',
        'admins': 'Admins',
        'administrator': 'Admins',
        'staff': 'Staff',
        'front desk': 'Staff',
        'frontdesk': 'Staff',
        'front desk team': 'Staff',
        'user': 'Users',
        'users': 'Users',
    }
    for profile in UserProfile.objects.all():
        role = (profile.role or '').strip().lower()
        if role in mapping:
            new_role = mapping[role]
            if profile.role != new_role:
                profile.role = new_role
                profile.save(update_fields=['role'])


def backwards(apps, schema_editor):
    UserProfile = apps.get_model('hotel_app', 'UserProfile')
    reverse_mapping = {
        'Admins': 'admin',
        'Staff': 'staff',
        'Users': 'user',
    }
    for profile in UserProfile.objects.all():
        role = profile.role
        if role in reverse_mapping:
            profile.role = reverse_mapping[role]
            profile.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('hotel_app', '0003_section'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(blank=True, db_index=True, max_length=150, null=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]


