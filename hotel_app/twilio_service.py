"""
Twilio WhatsApp Service for Hotel Messaging System
"""

import logging
import os
import re
from twilio.rest import Client
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class TwilioService:
    """Twilio WhatsApp integration service"""
    
    def __init__(self):
        # Try to get from Django settings first, then from environment variables
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None) or os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None) or os.environ.get('TWILIO_AUTH_TOKEN')
        self.whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None) or os.environ.get('TWILIO_WHATSAPP_FROM')
        
        # Only initialize client if all credentials are available
        if self.account_sid and self.auth_token and self.whatsapp_from:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                self.client = None
        else:
            self.client = None
    
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
            
            # Send the message
            if self.client:
                message = self.client.messages.create(**message_params)
                
                logger.info(f"WhatsApp message sent successfully to {formatted_to}. SID: {message.sid}")
                return {
                    'success': True,
                    'message_id': message.sid,
                    'status': message.status,
                    'to': message.to,
                    'from': message.from_
                }
            else:
                return {
                    'success': False,
                    'error': 'Twilio client is not initialized'
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
        return bool(self.account_sid and self.auth_token and self.whatsapp_from and self.client)

# Global service instance (will be initialized even if not configured)
twilio_service = TwilioService()