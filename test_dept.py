"""Quick script to test data population"""
import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotel_app.models import Department

try:
    print("Testing Department creation...")
    dept, created = Department.objects.get_or_create(name='Test Dept')
    print(f"✓ Department: {dept.name}")
except Exception as e:
    print(f"✗ Error creating department:")
    print(traceback.format_exc())
