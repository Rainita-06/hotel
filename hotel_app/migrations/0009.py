from django.db import migrations
from django.db.models import Count


def remove_duplicates(apps, schema_editor):
    LocationFamily = apps.get_model('hotel_app', 'LocationFamily')
    Floor = apps.get_model('hotel_app', 'Floor')
    LocationType = apps.get_model('hotel_app', 'LocationType')
    Location = apps.get_model('hotel_app', 'Location')
    Building = apps.get_model('hotel_app', 'Building')

    # Helper: safe PK name
    def pk(model):
        return model._meta.pk.name

    # =====================================================
    # LocationFamily.name
    # =====================================================
    pk_name = pk(LocationFamily)
    for d in (
        LocationFamily.objects.values('name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    ):
        qs = LocationFamily.objects.filter(name=d['name']).order_by(pk_name)
        qs.exclude(**{pk_name: qs.first().pk}).delete()

    # =====================================================
    # Floor (building, floor_name)
    # =====================================================
    pk_name = pk(Floor)
    for d in (
        Floor.objects.values('building', 'floor_name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    ):
        qs = Floor.objects.filter(
            building=d['building'],
            floor_name=d['floor_name']
        ).order_by(pk_name)
        qs.exclude(**{pk_name: qs.first().pk}).delete()

    # =====================================================
    # LocationType (family, name)
    # =====================================================
    pk_name = pk(LocationType)
    for d in (
        LocationType.objects.values('family', 'name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    ):
        qs = LocationType.objects.filter(
            family=d['family'],
            name=d['name']
        ).order_by(pk_name)
        qs.exclude(**{pk_name: qs.first().pk}).delete()

    # =====================================================
    # Building.name
    # =====================================================
    pk_name = pk(Building)
    for d in (
        Building.objects.values('name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    ):
        qs = Building.objects.filter(name=d['name']).order_by(pk_name)
        qs.exclude(**{pk_name: qs.first().pk}).delete()

    # =====================================================
    # Location.name  (or adjust fields if composite)
    # =====================================================
    pk_name = pk(Location)
    for d in (
        Location.objects.values('name')
        .annotate(c=Count(pk_name))
        .filter(c__gt=1)
    ):
        qs = Location.objects.filter(name=d['name']).order_by(pk_name)
        qs.exclude(**{pk_name: qs.first().pk}).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hotel_app', '0008_locationfamily_image'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates),
    ]
