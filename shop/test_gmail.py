"""
Test script to verify Gmail email sending is working
Save this as test_gmail.py in your project root and run:
python manage.py shell < test_gmail.py
"""

from django.core.mail import send_mail
from django.conf import settings

print("=" * 60)
print("Testing Gmail Email Configuration")
print("=" * 60)
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email User: {settings.EMAIL_HOST_USER}")
print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
print("=" * 60)

try:
    print("\nSending test email...")
    send_mail(
        subject='Test Email from JejeHub 🎉',
        message='This is a test email to verify Gmail SMTP is working correctly.\n\nIf you received this, your email configuration is working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['bstoke021@gmail.com'],  # Change to your test email
        fail_silently=False,
    )
    print("✓ SUCCESS: Email sent successfully!")
    print("✓ Check your Gmail inbox (including spam folder)")
    print("=" * 60)
except Exception as e:
    print(f"✗ ERROR: Email sending failed!")
    print(f"Error: {str(e)}")
    print("=" * 60)
    print("\nTroubleshooting:")
    print("1. Make sure 2-Factor Authentication is enabled on your Google account")
    print("2. Verify you're using an App Password (not your regular Gmail password)")
    print("3. Check that the app password has no spaces")
    print("4. Ensure your Gmail account allows less secure app access")