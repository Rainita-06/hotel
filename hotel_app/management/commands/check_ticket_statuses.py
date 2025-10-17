import json
from django.core.management.base import BaseCommand
from hotel_app.models import ServiceRequest

class Command(BaseCommand):
    help = 'Check ticket statuses in the database'

    def handle(self, *args, **options):
        # Get all tickets and their statuses
        tickets = ServiceRequest.objects.all()
        
        self.stdout.write(f'Total tickets: {tickets.count()}')
        
        # Count tickets by status
        status_counts = {}
        for ticket in tickets:
            status = ticket.status
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
                
        self.stdout.write('Ticket counts by status:')
        for status, count in status_counts.items():
            self.stdout.write(f'  {status}: {count}')
            
        # Show some sample tickets
        self.stdout.write('\nSample tickets:')
        for ticket in tickets[:5]:
            self.stdout.write(f'  Ticket #{ticket.id}: {ticket.status} - {ticket.request_type.name if ticket.request_type else "No request type"}')