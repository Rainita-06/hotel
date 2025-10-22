from django.core.management.base import BaseCommand
from hotel_app.models import SLAConfiguration

class Command(BaseCommand):
    help = 'Display current SLA configurations'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('\nCurrent SLA Configurations:')
        )
        self.stdout.write(
            '=' * 50
        )
        
        configs = SLAConfiguration.objects.all().order_by('priority')
        
        if not configs.exists():
            self.stdout.write(
                self.style.WARNING('No SLA configurations found. Run "python manage.py init_sla_config" to initialize.')
            )
            return
            
        # Header
        self.stdout.write(
            f"{'Priority':<12} {'Response Time':<15} {'Resolution Time':<15}"
        )
        self.stdout.write(
            '-' * 50
        )
        
        # Data rows
        for config in configs:
            self.stdout.write(
                f"{config.get_priority_display():<12} "
                f"{config.response_time_minutes} min{'':<8} "
                f"{config.resolution_time_minutes} min"
            )
            
        self.stdout.write(
            '=' * 50
        )
        self.stdout.write(
            self.style.SUCCESS('SLA configurations displayed successfully.')
        )