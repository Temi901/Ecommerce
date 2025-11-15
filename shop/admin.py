from django.contrib import admin
from django.contrib import messages
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .email_service import send_order_shipped_email, send_order_delivered_email
from .models import Payment
from threading import Thread


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'created_at']
    list_filter = ['available', 'created_at', 'category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'available']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'email', 'status', 'total_amount', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    list_editable = ['status']
    search_fields = ['id', 'email', 'first_name', 'last_name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('Order Information', {
            'fields': ('status', 'total_amount', 'tracking_number', 'carrier')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered']
    
    def save_model(self, request, obj, form, change):
        """Override save_model to send emails asynchronously when status changes"""
        if change:  # Only for existing orders (not new ones)
            try:
                # Get the original object from database
                old_obj = Order.objects.get(pk=obj.pk)
                old_status = old_obj.status
                new_status = obj.status
                
                # Save the order first
                super().save_model(request, obj, form, change)
                
                # Send email asynchronously if status changed
                if old_status != new_status:
                    if new_status == 'shipped':
                        try:
                            # Send email in background thread to prevent timeout
                            Thread(
                                target=send_order_shipped_email, 
                                args=(obj, obj.tracking_number, obj.carrier)
                            ).start()
                            messages.success(request, f'Order #{obj.id} marked as shipped. Email being sent to {obj.email}')
                        except Exception as e:
                            messages.warning(request, f'Order updated but email failed: {str(e)}')
                    elif new_status == 'delivered':
                        try:
                            # Send email in background thread to prevent timeout
                            Thread(
                                target=send_order_delivered_email, 
                                args=(obj,)
                            ).start()
                            messages.success(request, f'Order #{obj.id} marked as delivered. Email being sent to {obj.email}')
                        except Exception as e:
                            messages.warning(request, f'Order updated but email failed: {str(e)}')
            except Order.DoesNotExist:
                # If we can't get the old object, just save normally
                super().save_model(request, obj, form, change)
        else:
            # New order, just save normally
            super().save_model(request, obj, form, change)
    
    def mark_as_processing(self, request, queryset):
        """Mark selected orders as processing"""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as Processing.')
    mark_as_processing.short_description = "Mark selected orders as Processing"
    
    def mark_as_shipped(self, request, queryset):
        """Mark selected orders as shipped and send email notifications asynchronously"""
        updated = 0
        failed = 0
        for order in queryset:
            if order.status in ['pending', 'processing']:
                order.status = 'shipped'
                order.save()
                
                # Send shipped email asynchronously
                try:
                    Thread(
                        target=send_order_shipped_email, 
                        args=(order, order.tracking_number, order.carrier)
                    ).start()
                    updated += 1
                except Exception as e:
                    failed += 1
                    messages.warning(request, f'Order #{order.id}: Email failed - {str(e)}')
        
        if updated > 0:
            messages.success(request, f'{updated} order(s) marked as shipped. Emails being sent.')
        if failed > 0:
            messages.error(request, f'{failed} order(s) updated but emails failed.')
    mark_as_shipped.short_description = "Mark as Shipped and Send Email"
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected orders as delivered and send email notifications asynchronously"""
        updated = 0
        failed = 0
        for order in queryset:
            if order.status == 'shipped':
                order.status = 'delivered'
                order.save()
                
                # Send delivered email asynchronously
                try:
                    Thread(
                        target=send_order_delivered_email, 
                        args=(order,)
                    ).start()
                    updated += 1
                except Exception as e:
                    failed += 1
                    messages.warning(request, f'Order #{order.id}: Email failed - {str(e)}')
        
        if updated > 0:
            messages.success(request, f'{updated} order(s) marked as delivered. Emails being sent.')
        if failed > 0:
            messages.error(request, f'{failed} order(s) updated but emails failed.')
    mark_as_delivered.short_description = "Mark as Delivered and Send Email"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'tx_ref', 
        'order', 
        'amount', 
        'currency', 
        'status', 
        'payment_method',
        'created_at'
    ]
    list_filter = [
        'status', 
        'currency', 
        'payment_method',
        'created_at'
    ]
    search_fields = [
        'tx_ref', 
        'transaction_id', 
        'order__id',
        'order__email'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'flutterwave_response'
    ]
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'order', 
                'tx_ref', 
                'transaction_id', 
                'status'
            )
        }),
        ('Amount Details', {
            'fields': (
                'amount', 
                'currency', 
                'payment_method'
            )
        }),
        ('Response Data', {
            'fields': ('flutterwave_response',),
            'classes': ('collapse',),
            'description': 'Full response from Flutterwave API'
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at'
            )
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of payments"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of payment records"""
        return request.user.is_superuser