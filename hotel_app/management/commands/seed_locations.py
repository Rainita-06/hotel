import os
import random
import requests

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings

from hotel_app.models import (
    Building,
    Floor,
    LocationFamily,
    LocationType,
    Location,
)

# -----------------------------------------------------
# GLOBAL HOTEL IMAGES (361×192)
# -----------------------------------------------------
BUILDING_IMAGE_URLS = [
    "https://images.pexels.com/photos/261146/pexels-photo-261146.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271689/pexels-photo-271689.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/3586960/pexels-photo-3586960.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]

TYPE_IMAGE_URLS = [
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261395/pexels-photo-261395.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/189296/pexels-photo-189296.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271639/pexels-photo-271639.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261411/pexels-photo-261411.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271618/pexels-photo-271618.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]

FAMILY_IMAGE_URLS = [
    "https://images.pexels.com/photos/262048/pexels-photo-262048.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261395/pexels-photo-261395.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/189296/pexels-photo-189296.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271639/pexels-photo-271639.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]


class Command(BaseCommand):
    help = "Seed base hotel location data (6X format)"

    # -----------------------------------------------------
    # IMAGE HELPERS
    # -----------------------------------------------------

    def download_and_assign(self, obj, url_list, folder_name):
        try:
            url = random.choice(url_list)
            filename = url.split("/")[-1].split("?")[0]

            folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            response = requests.get(
                url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status_code == 200:
                obj.image.save(
                    f"{folder_name}/{filename}",
                    ContentFile(response.content),
                    save=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Image assigned → {obj}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Failed to download {url}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Image error: {e}")
            )

    # -----------------------------------------------------
    # MAIN COMMAND
    # -----------------------------------------------------

    def handle(self, *args, **kwargs):

        self.stdout.write(
            self.style.SUCCESS("\nAuto-generating Base Location Set (6X Format)…\n")
        )

        # -----------------------------------------------------
        # 1️⃣ BUILDINGS
        # -----------------------------------------------------
        building_names = [
            ("Main Building", "Primary building"),
            ("Royal Residency", "Luxury stay"),
            ("Garden Block", "Nature view rooms"),
            ("Sky Tower", "Top view suites"),
            ("Heritage Wing", "Classic architecture"),
            ("Elite Chamber", "VIP exclusive block"),
        ]

        buildings = []

        for name, desc in building_names:
            building, created = Building.objects.get_or_create(
                name=name,
                defaults={"description": desc},
            )

            self.stdout.write(
                f"{name} → {'CREATED' if created else 'Already Exists'}"
            )

            if not building.image:
                self.download_and_assign(
                    building, BUILDING_IMAGE_URLS, "building_images"
                )

            buildings.append(building)

        # -----------------------------------------------------
        # 2️⃣ FLOORS
        # -----------------------------------------------------
        floors = []

        for idx, b in enumerate(buildings, start=1):
            floor, created = Floor.objects.get_or_create(
                building=b,
                floor_name=f"Floor {idx}",
                defaults={"floor_number": idx},
            )

            self.stdout.write(
                f"Floor {idx} ({b.name}) → "
                f"{'CREATED' if created else 'Already Exists'}"
            )

            floors.append(floor)

        # -----------------------------------------------------
        # 3️⃣ FAMILIES
        # -----------------------------------------------------
        family_names = [
            "Guest Room",
            "Service Area",
            "Executive",
            "Premium",
            "Dining",
            "General Utility",
        ]

        families = []

        for name in family_names:
            family, created = LocationFamily.objects.get_or_create(name=name)

            self.stdout.write(
                f"{name} → {'CREATED' if created else 'Already Exists'}"
            )

            if not family.image:
                self.download_and_assign(
                    family, FAMILY_IMAGE_URLS, "location_families"
                )

            families.append(family)

        # -----------------------------------------------------
        # 4️⃣ TYPES
        # -----------------------------------------------------
        type_names = [
            "Deluxe Room",
            "Suite Room",
            "Lobby",
            "Dining Hall",
            "Executive Suite",
            "Conference Hall",
        ]

        types = []

        for i, type_name in enumerate(type_names):
            type_obj, created = LocationType.objects.get_or_create(
                name=type_name,
                family=families[i],
            )

            self.stdout.write(
                f"{type_name} → {'CREATED' if created else 'Already Exists'}"
            )

            if not type_obj.image:
                self.download_and_assign(
                    type_obj, TYPE_IMAGE_URLS, "type_images"
                )

            types.append(type_obj)

        # -----------------------------------------------------
        # 5️⃣ LOCATIONS
        # -----------------------------------------------------
        for i, b in enumerate(buildings):
            location, created = Location.objects.get_or_create(
                name=str(101 + i),
                building=b,
                floor=floors[i],
                family=types[i].family,
                type=types[i],
            )

            self.stdout.write(
                f"Location {location.name} ({b.name}) → "
                f"{'CREATED' if created else 'Already Exists'}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\nSUCCESS → Buildings | Floors | Families | Types | Locations READY\n"
            )
        )
