from django.db import migrations
from django.db.models import Count


def remove_location_duplicates(apps, schema_editor):
    Location = apps.get_model('hotel_app', 'Location')
    pk_name = Location._meta.pk.name

    duplicates = (
        Location.objects
        .values( 'name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    )

    for d in duplicates:
        qs = (
            Location.objects
            .filter( name=d['name'])
            .order_by(pk_name)
        )

        # keep the first, delete the rest
        qs.exclude(**{pk_name: qs.first().pk}).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hotel_app', '0010_floor_unique_floor_per_building_and_more'),  # adjust if needed
    ]

    operations = [
        migrations.RunPython(remove_location_duplicates),
    ]
