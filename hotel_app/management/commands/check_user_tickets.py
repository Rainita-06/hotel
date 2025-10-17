import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hotel_app.models import ServiceRequest

class Command(BaseCommand):
    help = 'Check tickets for a specific user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to check tickets for')

    def handle(self, *args, **options):
        username = options['username']
        if not username:
            self.stdout.write('Please provide a username with --username')
            return
            
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(f'User {username} not found')
            return
            
        # Get tickets assigned to this user or requested by this user
        assigned_tickets = ServiceRequest.objects.filter(assignee_user=user)
        requested_tickets = ServiceRequest.objects.filter(requester_user=user)
        
        self.stdout.write(f'User: {user.username}')
        self.stdout.write(f'Assigned tickets: {assigned_tickets.count()}')
        self.stdout.write(f'Requested tickets: {requested_tickets.count()}')
        
        # Count assigned tickets by status
        if assigned_tickets.exists():
            self.stdout.write('\nAssigned tickets by status:')
            status_counts = {}
            for ticket in assigned_tickets:
                status = ticket.status
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
                    
            for status, count in status_counts.items():
                self.stdout.write(f'  {status}: {count}')
                
        # Count requested tickets by status
        if requested_tickets.exists():
            self.stdout.write('\nRequested tickets by status:')
            status_counts = {}
            for ticket in requested_tickets:
                status = ticket.status
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
                    
            for status, count in status_counts.items():
                self.stdout.write(f'  {status}: {count}')