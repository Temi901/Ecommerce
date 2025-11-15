from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'shop'

urlpatterns = [
    # Core shop views
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart functionality
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Order functionality
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('reorder/<int:order_id>/', views.reorder_items, name='reorder_items'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('orders/<int:order_id>/tracking/', views.order_tracking, name='order_tracking'),
    path('orders/<int:order_id>/review/', views.order_review, name='order_review'),

    # Payment URLs
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    
    # User account
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('account/settings/', views.account_settings, name='account_settings'),
    path('account/password/change/', views.custom_password_change, name='custom_password_change'),
    
    # Authentication
    path('logout/', auth_views.LogoutView.as_view(next_page='shop:home'), name='logout'),
    
    # Password reset URLs
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name="registration/password_reset_form.html"
         ), 
         name="password_reset"),
         
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name="registration/password_reset_done.html"
         ), 
         name="password_reset_done"),
         
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name="registration/password_reset_confirm.html"
         ), 
         name="password_reset_confirm"),
         
    path('password_reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name="registration/password_reset_complete.html"
         ), 
         name="password_reset_complete"),
    
    # Legal pages
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('test-email-now/', views.test_email_view, name='test_email'),
]