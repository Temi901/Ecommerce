from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Payment
from .forms import CheckoutForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from datetime import datetime
import json
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .email_service import send_order_processing_email 
from threading import Thread
from .payment_service import FlutterwavePayment
from decimal import Decimal


@login_required
def profile(request):
    """
    Renders the user's profile page with order history.
    """
    return render(request, 'registration/profile.html', {
        'title': 'My Profile - JejeHub',
    })


@login_required
def account_settings(request):
    """
    Account settings view for updating profile information and preferences.
    """
    if request.method == 'POST':
        print("POST request received")
        print("POST data:", request.POST)
        
        # Handle profile update (first name, last name, email)
        if 'update_profile' in request.POST or ('first_name' in request.POST and 'last_name' in request.POST):
            print("Update profile triggered")
            
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            
            print(f"First Name: {first_name}")
            print(f"Last Name: {last_name}")
            print(f"Email: {email}")
            
            # Validate email
            if not email:
                messages.error(request, 'Email address is required.')
                return redirect('shop:account_settings')
            
            # Update user information
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            
            # Check if email is already taken by another user
            if email != user.email:
                if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                    messages.error(request, 'This email is already in use by another account.')
                    return redirect('shop:account_settings')
                else:
                    user.email = email
            else:
                user.email = email
            
            try:
                user.save()
                print(f"User saved successfully: {user.first_name} {user.last_name} - {user.email}")
                messages.success(request, 'Your profile has been updated successfully!')
            except Exception as e:
                print(f"Error saving user: {e}")
                messages.error(request, f'Error updating profile: {str(e)}')
            
            return redirect('shop:account_settings')
        
        # Handle notification preferences update
        elif 'update_notifications' in request.POST:
            email_notifications = 'email_notifications' in request.POST
            promotional_emails = 'promotional_emails' in request.POST
            
            print(f"Email notifications: {email_notifications}")
            print(f"Promotional emails: {promotional_emails}")
            
            # Store preferences in session
            request.session['email_notifications'] = email_notifications
            request.session['promotional_emails'] = promotional_emails
            request.session.modified = True  # Force session to save
            
            messages.success(request, 'Notification preferences updated successfully!')
            return redirect('shop:account_settings')
        
        # Handle account deletion
        elif 'delete_account' in request.POST:
            user = request.user
            username = user.username
            
            # Delete user
            logout(request)
            user.delete()
            
            messages.success(request, f'Account for {username} has been deleted successfully.')
            return redirect('shop:home')
    
    # Get notification preferences from session (default to True for email_notifications)
    email_notifications = request.session.get('email_notifications', True)
    promotional_emails = request.session.get('promotional_emails', False)
    
    print(f"Loading settings - Email notifications: {email_notifications}, Promotional: {promotional_emails}")
    
    context = {
        'title': 'Account Settings - JejeHub',
        'email_notifications': email_notifications,
        'promotional_emails': promotional_emails,
    }
    
    return render(request, 'shop/account_settings.html', context)



@login_required
def custom_password_change(request):
    """
    Handle password change from account settings.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Keep user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('shop:account_settings')
        else:
            # Display form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
            return redirect('shop:account_settings')
    
    # Redirect back to account settings for GET requests
    return redirect('shop:account_settings')


@login_required
def order_history(request):
    orders_list = Order.objects.filter(
        user=request.user
    ).select_related().prefetch_related('items__product').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        orders_list = orders_list.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(orders_list, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Calculate statistics (for ALL orders, not just filtered/paginated ones)
    all_orders = Order.objects.filter(user=request.user)
    
    stats = {
        'total_count': all_orders.count(),  # Total number of orders
        'delivered_count': all_orders.filter(status='delivered').count(),
        'shipped_count': all_orders.filter(status='shipped').count(),
        'total_spent': all_orders.aggregate(total=Sum('total_amount'))['total'] or 0,  # Handle None
    }
    
    context = {
        'orders': orders,
        **stats,  # This unpacks all stats into the context
    }
    
    return render(request, 'shop/order_history.html', context)


@login_required
def order_detail(request, order_id):
    """Detailed view of a single order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.select_related('product'),
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
@require_POST
def reorder_items(request, order_id):
    """Add all items from an order back to cart"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Get or create cart for user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        items_added = 0
        items_unavailable = []
        
        for order_item in order.items.all():
            product = order_item.product
            
            # Check if product is still available
            if product.stock >= order_item.quantity:
                # Check if item already in cart
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': order_item.quantity}
                )
                
                if not created:
                    # Update quantity if item already in cart
                    new_quantity = cart_item.quantity + order_item.quantity
                    if product.stock >= new_quantity:
                        cart_item.quantity = new_quantity
                        cart_item.save()
                    else:
                        # Add maximum available quantity
                        cart_item.quantity = product.stock
                        cart_item.save()
                        items_unavailable.append(f"{product.name} (limited stock)")
                
                items_added += 1
            else:
                items_unavailable.append(f"{product.name} (out of stock)")
        
        if items_added > 0:
            message = f"{items_added} items added to cart successfully!"
            if items_unavailable:
                message += f" Note: {len(items_unavailable)} items were unavailable or had limited stock."
            
            return JsonResponse({
                'success': True,
                'message': message,
                'items_added': items_added,
                'items_unavailable': items_unavailable
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No items could be added to cart. All items are currently unavailable.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing reorder: {str(e)}'
        })


@login_required
@require_POST
def cancel_order(request, order_id):
    """Cancel an order if it's still pending or processing"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if order can be cancelled
        if order.status not in ['pending', 'processing']:
            return JsonResponse({
                'success': False,
                'message': f'Cannot cancel order with status: {order.get_status_display()}'
            })
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Restore stock for all items in the order
        for order_item in order.items.all():
            product = order_item.product
            product.stock += order_item.quantity
            product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Order cancelled successfully. Refund will be processed within 5-7 business days.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error cancelling order: {str(e)}'
        })


@login_required
def download_invoice(request, order_id):
    """Generate and download invoice for an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # In a real application, you would generate a PDF invoice here
    # For now, we'll redirect back with a message
    messages.info(request, 'Invoice download feature coming soon!')
    return redirect('shop:order_detail', order_id=order_id)


@login_required
def order_tracking(request, order_id):
    """Track order status and shipping information"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # In a real application, you would integrate with shipping APIs
    tracking_info = {
        'order': order,
        'tracking_number': f'TRK{order.id}123456',
        'carrier': 'FastShip Express',
        'estimated_delivery': order.created_at.date(),
        'tracking_events': [
            {
                'status': 'Order Placed',
                'date': order.created_at,
                'location': 'Online Store',
                'description': 'Your order has been received and is being processed.'
            },
        ]
    }
    
    if order.status in ['processing', 'shipped', 'delivered']:
        tracking_info['tracking_events'].append({
            'status': 'Processing',
            'date': order.updated_at,
            'location': 'Fulfillment Center',
            'description': 'Your order is being prepared for shipment.'
        })
    
    if order.status in ['shipped', 'delivered']:
        tracking_info['tracking_events'].append({
            'status': 'Shipped',
            'date': order.updated_at,
            'location': 'Shipping Facility',
            'description': 'Your package is on its way to you.'
        })
    
    if order.status == 'delivered':
        tracking_info['tracking_events'].append({
            'status': 'Delivered',
            'date': order.updated_at,
            'location': 'Your Address',
            'description': 'Package has been delivered successfully.'
        })
    
    return render(request, 'shop/order_tracking.html', tracking_info)


@login_required
def order_review(request, order_id):
    """Allow users to review products from delivered orders"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'delivered':
        messages.error(request, 'You can only review products from delivered orders.')
        return redirect('shop:order_detail', order_id=order_id)
    
    if request.method == 'POST':
        # Handle review submission
        messages.success(request, 'Thank you for your review!')
        return redirect('shop:order_detail', order_id=order_id)
    
    context = {
        'order': order,
        'order_items': order.items.select_related('product'),
    }
    
    return render(request, 'shop/order_review.html', context)


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def home(request):
    featured_products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    
    # Safely handle search query
    search_query = request.GET.get('q', '')
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'search_query': search_query,
    }
    
    return render(request, 'shop/home.html', context)   


def product_list(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # Category filtering
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'shop/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'query': query
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]
    
    # Calculate savings if there's a sale price
    savings = None
    if hasattr(product, 'sale_price') and product.sale_price and product.sale_price < product.price:
        savings = product.price - product.sale_price
    
    context = {
        'product': product,
        'related_products': related_products,
        'savings': savings,
    }
    return render(request, 'shop/product_detail.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('shop:product_detail', slug=product.slug)


def cart_detail(request):
    cart = get_or_create_cart(request)
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def update_cart(request):
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        
        for item in cart.items.all():
            quantity = request.POST.get(f'quantity_{item.id}')
            if quantity:
                quantity = int(quantity)
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                else:
                    item.delete()
        
        messages.success(request, 'Cart updated!')
    
    return redirect('shop:cart_detail')


def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('shop:cart_detail')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Only set is_staff=False for NEW users being registered
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('shop:home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def terms_of_service(request):
    """Renders the terms of service page."""
    return render(request, 'shop/terms_of_service.html')


def privacy_policy(request):
    """Renders the privacy policy page."""
    return render(request, 'shop/privacy_policy.html')


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return render(request, 'registration/logout.html')
    else:
        return render(request, 'registration/logout_confirm.html')


def login_view(request):
    """Enhanced login view"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(
                    request, 
                    f'Welcome back, {user.first_name or user.username}!'
                )
                
                next_url = request.GET.get('next', 'shop:home')
                if next_url.startswith('/'):
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {

        'form': form,
        'title': 'Login - JejeHub',
    })


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            login(request, user)
            messages.success(request, f'Welcome to JejeHub, {username}!')
            return redirect('shop:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {

        'form': form,
        'title': 'Create Account - JejeHub',
    })


def products(request):
    """Products listing view"""
    return render(request, 'shop/products.html', {
        'title': 'Products - JejeHub',
    })


def cart(request):
    """Shopping cart view"""
    return render(request, 'shop/cart.html', {
        'title': 'Shopping Cart - JejeHub',
    })

@login_required
def checkout(request):
    """Modified checkout to initialize payment with dynamic currency"""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('shop:cart_detail')
    
    # Calculate cart subtotal (in USD) - this returns a Decimal
    subtotal_usd = cart.get_total_price()
    
    # Get exchange rate from settings
    exchange_rate = settings.EXCHANGE_RATE_USD_TO_NGN
    
    # Convert to NGN for fee calculations
    subtotal_ngn = subtotal_usd * exchange_rate
    
    # Calculate shipping fee based on order total (in NGN)
    if subtotal_ngn < settings.SHIPPING_THRESHOLD_NGN:
        shipping_fee_ngn = settings.SHIPPING_FEE_LOW_NGN
    else:
        shipping_fee_ngn = settings.SHIPPING_FEE_HIGH_NGN
    
    # Calculate tax
    if subtotal_ngn >= settings.TAX_THRESHOLD_NGN:
        tax_ngn = settings.TAX_AMOUNT_NGN
    else:
        tax_ngn = Decimal('0')
    
    # Convert fees back to USD for database storage
    shipping_fee_usd = shipping_fee_ngn / exchange_rate
    tax_usd = tax_ngn / exchange_rate
    
    # Calculate final total - now all values are Decimal
    total_usd = subtotal_usd + shipping_fee_usd + tax_usd
    total_ngn = subtotal_ngn + shipping_fee_ngn + tax_ngn
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order with fees included
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = total_usd  # Save total including fees
            order.status = 'pending'
            order.save()
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
            
            # Initialize Flutterwave payment with dynamic currency detection
            payment_result = FlutterwavePayment.initialize_payment(order, request)
            
            if payment_result['success']:
                # Create payment record with detected currency and converted amount
                Payment.objects.create(
                    order=order,
                    tx_ref=payment_result['tx_ref'],
                    amount=payment_result['amount'],
                    currency=payment_result['currency'],
                    status='pending'
                )
                
                return redirect(payment_result['payment_link'])
            else:
                messages.error(request, f"Payment initialization failed: {payment_result['error']}")
                order.delete()
                return redirect('shop:checkout')
    else:
        form = CheckoutForm()
    
    context = {
        'form': form,
        'cart': cart,
        'title': 'Checkout - JejeHub',
        'subtotal_usd': subtotal_usd,
        'subtotal_ngn': subtotal_ngn,
        'shipping_fee_usd': shipping_fee_usd,
        'shipping_fee_ngn': shipping_fee_ngn,
        'tax_usd': tax_usd,
        'tax_ngn': tax_ngn,
        'total_usd': total_usd,
        'total_ngn': total_ngn,
    }
    
    return render(request, 'shop/checkout.html', context)

@require_http_methods(["GET"])
def payment_callback(request):
    """Handle Flutterwave payment callback"""
    transaction_id = request.GET.get('transaction_id')
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')
    
    if not transaction_id:
        messages.error(request, 'Invalid payment response')
        return redirect('shop:home')
    
    # Verify payment
    verification = FlutterwavePayment.verify_payment(transaction_id)
    
    if verification['success'] and verification['status'] == 'successful':
        try:
            # Update payment record
            payment = Payment.objects.get(tx_ref=tx_ref)
            payment.transaction_id = transaction_id
            payment.status = 'successful'
            payment.flutterwave_response = verification
            payment.save()
            
            # Update order
            order = payment.order
            order.status = 'processing'
            order.save()
            
            # Send confirmation email asynchronously to avoid timeout
            try:
                Thread(target=send_order_processing_email, args=(order,)).start()
            except Exception as e:
                print(f"Email error: {e}")
            
            # Clear cart
            cart = get_or_create_cart(request)
            cart.items.all().delete()
            
            messages.success(request, f'Payment successful! Order #{order.id} has been placed.')
            return redirect('shop:order_detail', order_id=order.id)
            
        except Payment.DoesNotExist:
            messages.error(request, 'Payment record not found')
            return redirect('shop:home')
    else:
        # Payment failed or cancelled
        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
            payment.status = 'failed' if status == 'failed' else 'cancelled'
            payment.flutterwave_response = verification
            payment.save()
            
            order = payment.order
            order.status = 'cancelled'
            order.save()
        except Payment.DoesNotExist:
            pass
        
        messages.error(request, 'Payment was not successful. Please try again.')
        return redirect('shop:cart_detail')
@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Handle Flutterwave webhook for payment notifications"""
    
    # Verify webhook signature
    signature = request.headers.get('verif-hash')
    
    if signature != settings.FLUTTERWAVE_WEBHOOK_SECRET:
        return HttpResponse(status=401)
    
    try:
        payload = json.loads(request.body)
        
        # Extract payment data
        tx_ref = payload.get('data', {}).get('tx_ref')
        transaction_id = payload.get('data', {}).get('id')
        status = payload.get('data', {}).get('status')
        
        # Update payment record
        payment = Payment.objects.get(tx_ref=tx_ref)
        payment.transaction_id = transaction_id
        payment.status = 'successful' if status == 'successful' else 'failed'
        payment.flutterwave_response = payload
        payment.save()
        
        # Update order
        if status == 'successful':
            order = payment.order
            order.status = 'processing'
            order.save()
            
            # Send email notification
            try:
                send_order_processing_email(order)
            except Exception as e:
                print(f"Email error: {e}")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return HttpResponse(status=400)