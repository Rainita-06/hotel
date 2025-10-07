from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hotel_app.models import Notification
from hotel_app.utils import create_notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test notification for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create notification for')
        parser.add_argument('--title', type=str, default='Test Notification', help='Notification title')
        parser.add_argument('--message', type=str, default='This is a test notification', help='Notification message')
        parser.add_argument('--type', type=str, default='info', help='Notification type')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'])
            notification = create_notification(
                recipient=user,
                title=options['title'],
                message=options['message'],
                notification_type=options['type']
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created notification for {user.username} with ID {notification.id}'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {options["username"]} does not exist')
            )