"""
Twilio WhatsApp Service for Hotel Messaging System
"""

import logging
import re
from typing import Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError, ProgrammingError
from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioService:
    """Twilio WhatsApp integration service"""

    def __init__(self):
        self.account_sid: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.api_key_sid: Optional[str] = None
        self.api_key_secret: Optional[str] = None
        self.whatsapp_from: Optional[str] = None
        self.test_to_number: Optional[str] = None
        self.client: Optional[Client] = None

        self._load_credentials()

    @staticmethod
    def _clean(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    def _load_credentials(self):
        """Initialise credentials from persisted Twilio settings or fall back to Django settings."""
        settings_obj = self._get_db_settings()

        if settings_obj:
            self.account_sid = self._clean(getattr(settings_obj, 'account_sid', None))
            self.auth_token = self._clean(getattr(settings_obj, 'auth_token', None))
            self.api_key_sid = self._clean(getattr(settings_obj, 'api_key_sid', None))
            self.api_key_secret = self._clean(getattr(settings_obj, 'api_key_secret', None))
            self.whatsapp_from = self._clean(getattr(settings_obj, 'whatsapp_from', None))
            self.test_to_number = self._clean(getattr(settings_obj, 'test_to_number', None))
        else:
            # Fallback for legacy configuration that used environment variables / settings
            self.account_sid = self._clean(getattr(settings, 'TWILIO_ACCOUNT_SID', None))
            self.auth_token = self._clean(getattr(settings, 'TWILIO_AUTH_TOKEN', None))
            self.api_key_sid = self._clean(getattr(settings, 'TWILIO_API_KEY_SID', None))
            self.api_key_secret = self._clean(getattr(settings, 'TWILIO_API_KEY_SECRET', None))
            self.whatsapp_from = self._clean(getattr(settings, 'TWILIO_WHATSAPP_FROM', None))
            self.test_to_number = self._clean(getattr(settings, 'TWILIO_TEST_TO_NUMBER', None))

        setattr(settings, 'TWILIO_ACCOUNT_SID', self.account_sid or '')
        setattr(settings, 'TWILIO_AUTH_TOKEN', self.auth_token or '')
        setattr(settings, 'TWILIO_API_KEY_SID', self.api_key_sid or '')
        setattr(settings, 'TWILIO_API_KEY_SECRET', self.api_key_secret or '')
        setattr(settings, 'TWILIO_WHATSAPP_FROM', self.whatsapp_from or '')
        setattr(settings, 'TWILIO_TEST_TO_NUMBER', self.test_to_number or '')

        self._initialize_client()

    @staticmethod
    def _get_db_settings():
        try:
            from hotel_app.models import TwilioSettings
        except Exception:
            return None

        try:
            return TwilioSettings.objects.first()
        except (OperationalError, ProgrammingError):
            return None

    def _initialize_client(self):
        """Initialise the Twilio client with the current credentials."""
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as exc:  # Twilio raises generic Exception on auth issues
                logger.error("Failed to initialize Twilio client: %s", exc)
                self.client = None
                return exc
        elif self.account_sid and self.api_key_sid and self.api_key_secret:
            try:
                self.client = Client(self.api_key_sid, self.api_key_secret, account_sid=self.account_sid)
            except Exception as exc:
                logger.error("Failed to initialize Twilio client with API key: %s", exc)
                self.client = None
                return exc
        else:
            self.client = None
        return None

    def _ensure_client(self):
        """Ensure a Twilio client instance exists before making API calls."""
        if self.client:
            return self.client

        error = self._initialize_client()
        if error:
            logger.error("Unable to create Twilio client with stored credentials: %s", error)
        return self.client

    def update_credentials(
        self,
        account_sid=None,
        auth_token=None,
        api_key_sid=None,
        api_key_secret=None,
        whatsapp_from=None,
        test_to_number=None,
        updated_by=None,
    ):
        """
        Update credentials at runtime and refresh the Twilio client.

        Args:
            account_sid (str | None): Twilio account SID.
            auth_token (str | None): Twilio auth token.
            api_key_sid (str | None): Twilio API Key SID.
            api_key_secret (str | None): Twilio API Key Secret.
            whatsapp_from (str | None): Default WhatsApp sender number.
            test_to_number (str | None): Optional default test recipient.
            updated_by (User | None): User performing the update (for auditing).
        """
        updates = {}
        requires_client_refresh = False

        if account_sid is not None:
            self.account_sid = self._clean(account_sid)
            setattr(settings, 'TWILIO_ACCOUNT_SID', self.account_sid or '')
            updates['account_sid'] = self.account_sid or ''
            requires_client_refresh = True

        if auth_token is not None:
            self.auth_token = self._clean(auth_token)
            setattr(settings, 'TWILIO_AUTH_TOKEN', self.auth_token or '')
            updates['auth_token'] = self.auth_token or ''
            requires_client_refresh = True

        if api_key_sid is not None:
            self.api_key_sid = self._clean(api_key_sid)
            setattr(settings, 'TWILIO_API_KEY_SID', self.api_key_sid or '')
            updates['api_key_sid'] = self.api_key_sid or ''
            requires_client_refresh = True

        if api_key_secret is not None:
            self.api_key_secret = self._clean(api_key_secret)
            setattr(settings, 'TWILIO_API_KEY_SECRET', self.api_key_secret or '')
            updates['api_key_secret'] = self.api_key_secret or ''
            requires_client_refresh = True

        if whatsapp_from is not None:
            self.whatsapp_from = self._clean(whatsapp_from)
            setattr(settings, 'TWILIO_WHATSAPP_FROM', self.whatsapp_from or '')
            updates['whatsapp_from'] = self.whatsapp_from or ''

        if test_to_number is not None:
            self.test_to_number = self._clean(test_to_number)
            setattr(settings, 'TWILIO_TEST_TO_NUMBER', self.test_to_number or '')
            updates['test_to_number'] = self.test_to_number or ''

        if updates or updated_by is not None:
            self._persist_credentials(updates, updated_by)

        if not requires_client_refresh:
            return

        error = self._initialize_client()
        if error:
            raise ImproperlyConfigured(f"Failed to initialize Twilio client: {error}")

    def _persist_credentials(self, updates, updated_by=None):
        if not updates and updated_by is None:
            return

        try:
            from hotel_app.models import TwilioSettings
        except Exception:
            return

        try:
            settings_obj, _ = TwilioSettings.objects.get_or_create(pk=1)
            for field, value in updates.items():
                setattr(settings_obj, field, value)
            update_fields = list(updates.keys())
            if updated_by is not None:
                settings_obj.updated_by = updated_by
                update_fields.append('updated_by')
            update_fields.append('updated_at')
            settings_obj.save(update_fields=update_fields)
        except (OperationalError, ProgrammingError) as exc:
            logger.warning("Unable to persist Twilio credentials: %s", exc)
    
    def _format_whatsapp_number(self, number):
        """
        Format a number as a WhatsApp number
        
        Args:
            number (str): Phone number
            
        Returns:
            str: Properly formatted WhatsApp number
        """
        # If it's already formatted as a WhatsApp number, return as is
        if number.startswith('whatsapp:'):
            return number
            
        # If it starts with '+', prepend 'whatsapp:'
        if number.startswith('+'):
            return f'whatsapp:{number}'
            
        # If it's a raw number, add default country code and format
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', number)
        
        # If it's 10 digits, assume it's a US number
        if len(digits_only) == 10:
            return f'whatsapp:+1{digits_only}'
            
        # If it's 11 digits and starts with 1, format as US number
        if len(digits_only) == 11 and digits_only.startswith('1'):
            return f'whatsapp:+{digits_only}'
            
        # For other cases, assume it already includes country code
        if not number.startswith('+'):
            return f'whatsapp:+{digits_only}'
            
        return f'whatsapp:{number}'
    
    def send_whatsapp_message(self, to_number, body=None, content_sid=None, content_variables=None):
        """
        Send a WhatsApp message using Twilio
        
        Args:
            to_number (str): Recipient's WhatsApp number
            body (str, optional): Plain text message body
            content_sid (str, optional): Content template SID
            content_variables (dict, optional): Variables for content template
            
        Returns:
            dict: Response with success status and message details
        """
        # Check if service is configured
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Twilio service is not properly configured'
            }
        
        try:
            # Format the numbers
            formatted_to = self._format_whatsapp_number(to_number)

            # Handle the from number
            if self.whatsapp_from:
                # Remove 'whatsapp:' prefix if present and re-add it
                from_number = self.whatsapp_from.replace('whatsapp:', '') if self.whatsapp_from.startswith('whatsapp:') else self.whatsapp_from
                formatted_from = self._format_whatsapp_number(from_number)
            else:
                formatted_from = self.whatsapp_from

            # Prepare message parameters
            message_params = {
                'from_': formatted_from,
                'to': formatted_to
            }
            
            # Add content template if provided
            if content_sid:
                message_params['content_sid'] = content_sid
                if content_variables:
                    message_params['content_variables'] = content_variables
            elif body:
                message_params['body'] = body
            else:
                raise ValueError("Either body or content_sid must be provided")

            client = self._ensure_client()
            if not client:
                return {
                    'success': False,
                    'error': 'Twilio client is not initialized'
                }

            message = client.messages.create(**message_params)

            logger.info(f"WhatsApp message sent successfully to {formatted_to}. SID: {message.sid}")
            return {
                'success': True,
                'message_id': message.sid,
                'status': message.status,
                'to': message.to,
                'from': message.from_
            }

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_template_message(self, to_number, content_sid, content_variables=None):
        """
        Send a WhatsApp message using a content template
        
        Args:
            to_number (str): Recipient's WhatsApp number
            content_sid (str): Content template SID
            content_variables (dict, optional): Variables for content template
            
        Returns:
            dict: Response with success status and message details
        """
        return self.send_whatsapp_message(
            to_number=to_number,
            content_sid=content_sid,
            content_variables=content_variables
        )
    
    def send_text_message(self, to_number, body):
        """
        Send a plain text WhatsApp message
        
        Args:
            to_number (str): Recipient's WhatsApp number
            body (str): Message body
            
        Returns:
            dict: Response with success status and message details
        """
        return self.send_whatsapp_message(to_number=to_number, body=body)
    
    def is_configured(self):
        """
        Check if Twilio service is properly configured
        
        Returns:
            bool: True if properly configured, False otherwise
        """
        credentials_ready = bool(
            (self.account_sid and self.auth_token)
            or (self.account_sid and self.api_key_sid and self.api_key_secret)
        )
        return bool(credentials_ready and self.whatsapp_from)

# Global service instance (will be initialized even if not configured)
twilio_service = TwilioService()