from django.core.management.base import BaseCommand
from hotel_app.models import Department, RequestType, DepartmentRequestSLA

class Command(BaseCommand):
    help = 'Initialize sample department/request-specific SLA configurations'

    def handle(self, *args, **options):
        # Get all departments and request types
        departments = Department.objects.all()
        request_types = RequestType.objects.all()
        
        if not departments.exists() or not request_types.exists():
            self.stdout.write(
                self.style.WARNING('No departments or request types found. Please create some first.')
            )
            return

        # Sample SLA configurations for different priority levels
        sample_configs = [
            {
                'priority': 'critical',
                'response_time_minutes': 3,  # 3 minutes for critical
                'resolution_time_minutes': 30  # 30 minutes for critical
            },
            {
                'priority': 'high',
                'response_time_minutes': 5,  # 5 minutes for high
                'resolution_time_minutes': 60  # 1 hour for high
            },
            {
                'priority': 'normal',
                'response_time_minutes': 10,  # 10 minutes for normal
                'resolution_time_minutes': 120  # 2 hours for normal
            },
            {
                'priority': 'low',
                'response_time_minutes': 15,  # 15 minutes for low
                'resolution_time_minutes': 240  # 4 hours for low
            }
        ]

        created_count = 0
        updated_count = 0

        # Create SLA configurations for each department/request type combination
        for department in departments:
            for request_type in request_types:
                for config_data in sample_configs:
                    config, created = DepartmentRequestSLA.objects.update_or_create(
                        department=department,
                        request_type=request_type,
                        priority=config_data['priority'],
                        defaults={
                            'response_time_minutes': config_data['response_time_minutes'],
                            'resolution_time_minutes': config_data['resolution_time_minutes']
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created SLA for {department.name} - {request_type.name} ({config_data["priority"]}): '
                                f'{config_data["response_time_minutes"]}min response, '
                                f'{config_data["resolution_time_minutes"]}min resolution'
                            )
                        )
                    else:
                        updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized department/request SLA configurations: '
                f'{created_count} created, {updated_count} updated'
            )
        )