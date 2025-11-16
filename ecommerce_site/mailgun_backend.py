# ecommerce_site/mailgun_backend.py
"""
Custom email backend that uses Mailgun's HTTP API instead of SMTP.
This avoids SMTP port blocking issues on platforms like Render.
"""
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class MailgunBackend(BaseEmailBackend):
    """
    Email backend that uses Mailgun's HTTP API instead of SMTP.
    This works on platforms that block SMTP ports (like Render's free tier).
    """
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects via Mailgun HTTP API.
        Returns the number of messages sent successfully.
        """
        if not email_messages:
            return 0
            
        num_sent = 0
        api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        
        if not api_key or not domain:
            if not self.fail_silently:
                raise ValueError("MAILGUN_API_KEY and MAILGUN_DOMAIN must be set in settings")
            return 0
        
        for message in email_messages:
            try:
                # Prepare the email data
                data = {
                    "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.body,
                }
                
                # Add HTML version if available
                if message.alternatives:
                    for content, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            data["html"] = content
                            break
                
                # Add CC if present
                if message.cc:
                    data["cc"] = message.cc
                
                # Add BCC if present
                if message.bcc:
                    data["bcc"] = message.bcc
                
                # Send via Mailgun API
                response = requests.post(
                    f"https://api.mailgun.net/v3/{domain}/messages",
                    auth=("api", api_key),
                    data=data,
                    timeout=10
                )
                
                # Check if successful
                if response.status_code == 200:
                    num_sent += 1
                elif not self.fail_silently:
                    raise Exception(f"Mailgun API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                if not self.fail_silently:
                    raise
                # Log the error if needed
                print(f"Email sending failed: {str(e)}")
        
        return num_sent