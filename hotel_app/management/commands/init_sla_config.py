from django.core.management.base import BaseCommand
from hotel_app.models import SLAConfiguration

class Command(BaseCommand):
    help = 'Initialize default SLA configurations'

    def handle(self, *args, **options):
        # Default SLA configurations as per requirements
        default_configs = [
            {
                'priority': 'critical',
                'response_time_minutes': 5,
                'resolution_time_minutes': 5
            },
            {
                'priority': 'high',
                'response_time_minutes': 10,
                'resolution_time_minutes': 10
            },
            {
                'priority': 'normal',
                'response_time_minutes': 15,
                'resolution_time_minutes': 15
            },
            {
                'priority': 'low',
                'response_time_minutes': 20,
                'resolution_time_minutes': 20
            }
        ]

        created_count = 0
        updated_count = 0

        for config_data in default_configs:
            config, created = SLAConfiguration.objects.update_or_create(
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
                        f'Created SLA configuration for {config_data["priority"]}: '
                        f'{config_data["response_time_minutes"]}min response, '
                        f'{config_data["resolution_time_minutes"]}min resolution'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated SLA configuration for {config_data["priority"]}: '
                        f'{config_data["response_time_minutes"]}min response, '
                        f'{config_data["resolution_time_minutes"]}min resolution'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized SLA configurations: '
                f'{created_count} created, {updated_count} updated'
            )
        )