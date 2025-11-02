   # shop/email_service.py
# Email notification system for Django e-commerce

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_order_processing_email(order):
    """Send email when order is being processed"""
    
    subject = f'Order #{order.id} is Being Processed'
    
    # Create the HTML email content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Order Processing Confirmation</h2>
        <p>Hi {order.first_name},</p>
        <p>Great news! We've received your order and it's now being processed.</p>
        
        <div style="background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
            <h3 style="margin-top: 0;">Order Details</h3>
            <p><strong>Order Number:</strong> #{order.id}</p>
            <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y')}</p>
            <p><strong>Total Amount:</strong> ₦{order.total_price:,.2f}</p>
        </div>
        
        <h4>Items Ordered:</h4>
        <ul>
            {''.join([f'<li>{item.product.name} - Quantity: {item.quantity} - ₦{item.price:,.2f}</li>' 
                     for item in order.items.all()])}
        </ul>
        
        <div style="background: #e3f2fd; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p><strong>Shipping Address:</strong></p>
            <p style="margin-left: 20px;">
                {order.first_name} {order.last_name}<br>
                {order.address}<br>
                {order.city}, {order.state} {order.postal_code}
            </p>
        </div>
        
        <p>We'll send you another email once your order has been shipped.</p>
        <p>Thank you for shopping with us!</p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">
            If you have any questions, please contact us at {settings.DEFAULT_FROM_EMAIL}
        </p>
    </body>
    </html>
    """
    
    # Plain text version
    plain_message = strip_tags(html_content)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_order_shipped_email(order, tracking_number=None, carrier=None):
    """Send email when order has been shipped"""
    
    subject = f'Order #{order.id} Has Been Shipped! 📦'
    
    tracking_info = ''
    if tracking_number:
        tracking_info = f"""
        <div style="background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #28a745;">
            <h3 style="margin-top: 0; color: #28a745;">Shipping Information</h3>
            <p><strong>Tracking Number:</strong> {tracking_number}</p>
            {f'<p><strong>Carrier:</strong> {carrier}</p>' if carrier else ''}
            <p><strong>Estimated Delivery:</strong> 3-5 business days</p>
        </div>
        """
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #28a745;">Your Order Has Been Shipped! 📦</h2>
        <p>Hi {order.first_name},</p>
        <p>Exciting news! Your order has been shipped and is on its way to you.</p>
        
        <div style="background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
            <h3 style="margin-top: 0;">Order Summary</h3>
            <p><strong>Order Number:</strong> #{order.id}</p>
            <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y')}</p>
            <p><strong>Total Amount:</strong> ₦{order.total_price:,.2f}</p>
        </div>
        
        {tracking_info}
        
        <h4>Shipping Address:</h4>
        <p style="margin-left: 20px;">
            {order.first_name} {order.last_name}<br>
            {order.address}<br>
            {order.city}, {order.state} {order.postal_code}
        </p>
        
        <h4>Items in Your Order:</h4>
        <ul>
            {''.join([f'<li>{item.product.name} - Quantity: {item.quantity}</li>' 
                     for item in order.items.all()])}
        </ul>
        
        <p>Thank you for your order!</p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">
            If you have any questions, please contact us at {settings.DEFAULT_FROM_EMAIL}
        </p>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_order_delivered_email(order):
    """Send email when order has been delivered"""
    
    subject = f'Order #{order.id} Delivered Successfully! ✅'
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #28a745;">Your Order Has Been Delivered! ✅</h2>
        <p>Hi {order.first_name},</p>
        <p>We're happy to confirm that your order has been successfully delivered!</p>
        
        <div style="background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 5px;">
            <h3 style="margin-top: 0;">Order Details</h3>
            <p><strong>Order Number:</strong> #{order.id}</p>
            <p><strong>Delivered on:</strong> {order.updated_at.strftime('%B %d, %Y')}</p>
        </div>
        
        <p>We hope you love your purchase! If you have any issues or questions, please don't hesitate to reach out.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <p style="font-size: 18px; color: #333;">How was your experience?</p>
            <p style="color: #666;">We'd love to hear your feedback!</p>
        </div>
        
        <p>Thank you for choosing us!</p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">
            If you have any questions, please contact us at {settings.DEFAULT_FROM_EMAIL}
        </p>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False