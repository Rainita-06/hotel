from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import ServiceRequest, ServiceRequestStep, WorkflowStep


@shared_task
def process_service_request(request_id):
    """
    Process a new service request through its workflow
    """
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
        workflow = service_request.request_type.workflow

        if workflow:
            # Get the first workflow step
            first_step = workflow.workflowstep_set.order_by("step_order").first()
            if first_step:
                # Create initial service request step
                ServiceRequestStep.objects.create(
                    request=service_request,
                    step=first_step,
                    status="pending",
                )

                # Notify users if role_hint is defined
                if first_step.role_hint:
                    notify_step_assignment.delay(service_request.id, first_step.id)

    except ServiceRequest.DoesNotExist:
        # Log or handle gracefully
        return


@shared_task
def notify_step_assignment(request_id, step_id):
    """
    Notify assigned users about a new workflow step
    """
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
        step = WorkflowStep.objects.get(id=step_id)

        recipients = []

        if step.role_hint == "admin":
            from django.contrib.auth.models import Group

            try:
                admin_group = Group.objects.get(name="Admins")
                recipients = admin_group.user_set.all()
            except Group.DoesNotExist:
                recipients = []
        else:
            # Default to assignee
            if service_request.assignee_user:
                recipients = [service_request.assignee_user]

        # Send email notifications
        for user in recipients:
            if user and user.email:
                send_mail(
                    subject=f"New Task: {service_request.request_type.name}",
                    message=f'You have been assigned a new task: "{step.name}"',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

    except (ServiceRequest.DoesNotExist, WorkflowStep.DoesNotExist):
        return


@shared_task
def check_pending_requests():
    """
    Periodic task to check for stale pending requests
    """
    stale_threshold = timezone.now() - timedelta(hours=24)

    stale_steps = ServiceRequestStep.objects.filter(
        status="pending",
        started_at__lte=stale_threshold,
    )

    for step in stale_steps:
        notify_stale_request.delay(step.id)


@shared_task
def notify_stale_request(step_id):
    """
    Notify users about a stale service request step
    """
    try:
        step = ServiceRequestStep.objects.get(id=step_id)
        service_request = step.request

        recipients = []

        if service_request.assignee_user and service_request.assignee_user.email:
            recipients.append(service_request.assignee_user.email)
        else:
            from django.contrib.auth.models import Group

            try:
                admin_group = Group.objects.get(name="Admins")
                recipients += [
                    user.email
                    for user in admin_group.user_set.all()
                    if user.email
                ]
            except Group.DoesNotExist:
                pass

        if recipients:
            send_mail(
                subject=f"Service Request Step Pending: {service_request.request_type.name}",
                message=f'The step "{step.step.name}" has been pending for over 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )

    except ServiceRequestStep.DoesNotExist:
        return


@shared_task
def check_sla_breaches():
    """
    Periodic task to check for SLA breaches in service requests
    """
    from .models import ServiceRequest
    from django.contrib.auth import get_user_model
    from .utils import create_notification, create_bulk_notifications
    
    User = get_user_model()
    
    # Get all open service requests (not closed or completed)
    open_requests = ServiceRequest.objects.exclude(
        status__in=['completed', 'closed']
    ).select_related('requester_user', 'assignee_user', 'department', 'request_type')
    
    breach_count = 0
    for request in open_requests:
        # Store previous SLA status
        previous_response_breach = request.response_sla_breached
        previous_resolution_breach = request.resolution_sla_breached
        
        # Check SLA breaches
        request.check_sla_breaches()
        
        # Check if this is a new breach
        new_response_breach = request.response_sla_breached and not previous_response_breach
        new_resolution_breach = request.resolution_sla_breached and not previous_resolution_breach
        
        # If SLA was newly breached, send notifications
        if new_response_breach or new_resolution_breach:
            # Notify assignee if exists
            if request.assignee_user:
                breach_type = "Response" if new_response_breach else "Resolution"
                create_notification(
                    recipient=request.assignee_user,
                    title=f"SLA Breach Alert: Ticket #{request.id}",
                    message=f"{breach_type} SLA has been breached for ticket #{request.id}: {request.request_type.name}. Please take immediate action.",
                    notification_type='warning',
                    related_object=request
                )
            
            # Notify department staff if department exists
            if request.department:
                department_users = User.objects.filter(userprofile__department=request.department)
                if department_users.exists():
                    breach_type = "Response" if new_response_breach else "Resolution"
                    create_bulk_notifications(
                        recipients=department_users,
                        title=f"SLA Breach Alert: Ticket #{request.id}",
                        message=f"{breach_type} SLA has been breached for ticket #{request.id}: {request.request_type.name}. Please take immediate action.",
                        notification_type='warning',
                        related_object=request
                    )
            
            # Notify requester
            if request.requester_user:
                create_notification(
                    recipient=request.requester_user,
                    title=f"SLA Breach: Ticket #{request.id}",
                    message=f"Your ticket #{request.id} is experiencing delays. We're working to resolve it as quickly as possible.",
                    notification_type='warning',
                    related_object=request
                )
            
            breach_count += 1
        
        # Save the updated SLA status
        request.save()
    
    return f"Checked {open_requests.count()} open requests. Found {breach_count} new SLA breaches."
