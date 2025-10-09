import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from hotel_app.models import ServiceRequest

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for SLA breaches in service requests and send notifications'

    def handle(self, *args, **options):
        # Get all open service requests (not closed or completed)
        open_requests = ServiceRequest.objects.exclude(
            status__in=['completed', 'closed']
        ).select_related('requester_user', 'assignee_user', 'department', 'request_type')

        breach_count = 0
        for request in open_requests:
            # Check SLA breaches
            request.check_sla_breaches()
            
            # If SLA was breached, send notifications
            if request.sla_breached and (request.response_sla_breached or request.resolution_sla_breached):
                # Only send notification if this is a new breach
                if not getattr(request, '_sla_breach_notified', False):
                    self.notify_sla_breach(request)
                    breach_count += 1
            
            # Save the updated SLA status
            request.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully checked {open_requests.count()} open requests. '
                f'Found {breach_count} new SLA breaches.'
            )
        )

    def notify_sla_breach(self, service_request):
        """Send notifications for SLA breach"""
        from hotel_app.utils import create_notification, create_bulk_notifications
        
        # Mark this request as notified to avoid duplicate notifications
        service_request._sla_breach_notified = True
        
        # Notify assignee if exists
        if service_request.assignee_user:
            create_notification(
                recipient=service_request.assignee_user,
                title=f"SLA Breach Alert: Ticket #{service_request.id}",
                message=f"SLA has been breached for ticket #{service_request.id}: {service_request.request_type.name}. Please take immediate action.",
                notification_type='warning',
                related_object=service_request
            )
        
        # Notify department staff if department exists
        if service_request.department:
            department_users = User.objects.filter(userprofile__department=service_request.department)
            if department_users.exists():
                create_bulk_notifications(
                    recipients=department_users,
                    title=f"SLA Breach Alert: Ticket #{service_request.id}",
                    message=f"SLA has been breached for ticket #{service_request.id}: {service_request.request_type.name}. Please take immediate action.",
                    notification_type='warning',
                    related_object=service_request
                )
        
        # Notify requester
        if service_request.requester_user:
            create_notification(
                recipient=service_request.requester_user,
                title=f"SLA Breach: Ticket #{service_request.id}",
                message=f"Your ticket #{service_request.id} is experiencing delays. We're working to resolve it as quickly as possible.",
                notification_type='warning',
                related_object=service_request
            )