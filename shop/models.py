from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.conf import settings
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('shop:category_products', args=[self.slug])

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', blank=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])
    
    @property
    def image_url(self):
        """Get the proper Cloudinary URL"""
        if not self.image:
            return None
        
        image_str = str(self.image)
        
        # If it's already a full URL, return it
        if image_str.startswith('http'):
            return image_str
        
        # If it's a Cloudinary path, build the URL
        if image_str.startswith('products/product_'):
            cloud_name = 'dznwck80z'
            return f'https://res.cloudinary.com/{cloud_name}/image/upload/{image_str}'
        
        # Fallback to default Django media URL
        try:
            return self.image.url
        except:
            return None

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cart {self.id}"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Customer Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    
    # Order Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    user_order_number = models.IntegerField(default=1)  # ADD THIS LINE
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping Information
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    
    @property
    def total_price(self):
        """Alias for total_amount to match email template"""
        return self.total_amount
    
    def save(self, *args, **kwargs):
        # Auto-increment user_order_number for new orders only
        if not self.pk:  # Only for new orders
            last_order = Order.objects.filter(user=self.user).order_by('-user_order_number').first()
            if last_order:
                self.user_order_number = last_order.user_order_number + 1
            else:
                self.user_order_number = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Order #{self.user_order_number} - {self.get_status_display()}'
    
    class Meta:
        ordering = ['-created_at']
         
    def get_subtotal(self):
        """Calculate order subtotal (items only, no fees)"""
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_shipping_fee(self):
        """Calculate shipping fee based on subtotal"""
        subtotal = self.get_subtotal()
        exchange_rate = settings.EXCHANGE_RATE_USD_TO_NGN
        subtotal_ngn = subtotal * exchange_rate
        
        if subtotal_ngn < settings.SHIPPING_THRESHOLD_NGN:
            shipping_fee_ngn = settings.SHIPPING_FEE_LOW_NGN
        else:
            shipping_fee_ngn = settings.SHIPPING_FEE_HIGH_NGN
        
        return shipping_fee_ngn / exchange_rate
    
    def get_tax(self):
        """Calculate tax based on subtotal"""
        subtotal = self.get_subtotal()
        exchange_rate = settings.EXCHANGE_RATE_USD_TO_NGN
        subtotal_ngn = subtotal * exchange_rate
        
        if subtotal_ngn >= settings.TAX_THRESHOLD_NGN:
            tax_ngn = settings.TAX_AMOUNT_NGN
        else:
            tax_ngn = Decimal('0')
        
        return tax_ngn / exchange_rate
    
    def calculate_total(self):
        """Calculate total including all fees"""
        return self.get_subtotal() + self.get_shipping_fee() + self.get_tax()





class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        return self.quantity * self.price


# PAYMENT MODEL - ONLY ONE DEFINITION
class Payment(models.Model):
    """Payment model to track Flutterwave transactions"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    tx_ref = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Transaction reference from Flutterwave"
    )
    transaction_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Flutterwave transaction ID"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Amount paid"
    )
    currency = models.CharField(
        max_length=3, 
        default='USD',
        help_text="Currency code (USD, NGN, etc.)"
    )
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS, 
        default='pending'
    )
    payment_method = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Payment method used (card, bank transfer, etc.)"
    )
    flutterwave_response = models.JSONField(
        blank=True, 
        null=True,
        help_text="Full response from Flutterwave"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.tx_ref} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == 'successful'
    
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'pending'