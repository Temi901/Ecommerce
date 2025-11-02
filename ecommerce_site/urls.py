"""
URL configuration for ecommerce_site project.
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import HttpResponse


def favicon_view(request):
    return HttpResponse(status=204)


urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Favicon handler
    path('favicon.ico', favicon_view),
    
    # Custom Password Reset URLs (BEFORE accounts/)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             success_url=reverse_lazy('password_reset_done'),
             html_email_template_name='registration/password_reset_email.html',
         ),
         name='password_reset'
    ),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'
    ),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ), 
         name='password_reset_confirm'
    ),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'
    ),
    
    # Password change URLs
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change.html',
             success_url=reverse_lazy('custom_password_change_done')
         ), 
         name='custom_password_change'
    ),
    
    path('password-change-done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html'
         ), 
         name='custom_password_change_done'
    ),
    
    # Django authentication URLs (login, logout) - AFTER custom URLs
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Shop URLs (must be last)
    path('', include('shop.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)