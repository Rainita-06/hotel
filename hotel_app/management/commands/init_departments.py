from django.core.management.base import BaseCommand
from hotel_app.models import Department, UserGroup

class Command(BaseCommand):
    help = 'Initialize sample departments and user groups for the hotel management system'

    def handle(self, *args, **options):
        self.stdout.write(
            'Initializing sample departments and user groups...'
        )

        # Create sample departments
        departments_data = [
            {
                'name': 'Housekeeping',
                'description': 'Responsible for room cleaning, maintenance, and guest services'
            },
            {
                'name': 'Front Office',
                'description': 'Handles guest check-in, check-out, and front desk services'
            },
            {
                'name': 'Food & Beverage',
                'description': 'Manages restaurants, room service, and catering'
            },
            {
                'name': 'Maintenance',
                'description': 'Handles repairs, maintenance, and engineering services'
            },
            {
                'name': 'Security',
                'description': 'Responsible for guest safety and property security'
            },
            {
                'name': 'Concierge',
                'description': 'Provides guest services and local information'
            }
        ]

        created_departments = 0
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                created_departments += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {dept.name}')
                )

        # Create sample user groups associated with departments
        groups_data = [
            {
                'name': 'Housekeeping Supervisors',
                'description': 'Supervisors in the Housekeeping department',
                'department_name': 'Housekeeping'
            },
            {
                'name': 'Housekeeping Staff',
                'description': 'Staff members in the Housekeeping department',
                'department_name': 'Housekeeping'
            },
            {
                'name': 'Front Desk Agents',
                'description': 'Front desk staff members',
                'department_name': 'Front Office'
            },
            {
                'name': 'Restaurant Staff',
                'description': 'Staff in the Food & Beverage department',
                'department_name': 'Food & Beverage'
            },
            {
                'name': 'Maintenance Technicians',
                'description': 'Technicians in the Maintenance department',
                'department_name': 'Maintenance'
            },
            {
                'name': 'Security Officers',
                'description': 'Security personnel',
                'department_name': 'Security'
            },
            {
                'name': 'Concierge Team',
                'description': 'Concierge staff members',
                'department_name': 'Concierge'
            }
        ]

        created_groups = 0
        for group_data in groups_data:
            try:
                department = Department.objects.get(name=group_data['department_name'])
            except Department.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Department {group_data['department_name']} not found, skipping group creation")
                )
                continue

            group, created = UserGroup.objects.get_or_create(
                name=group_data['name'],
                defaults={
                    'description': group_data['description'],
                    'department': department
                }
            )
            if created:
                created_groups += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created user group: {group.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized {created_departments} departments and {created_groups} user groups!'
            )
        )