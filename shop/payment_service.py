import requests
import uuid
from django.conf import settings
from django.urls import reverse

class FlutterwavePayment:
    """Handle Flutterwave payment processing"""
    
    # Use constant instead of settings
    BASE_URL = "https://api.flutterwave.com/v3"
    
    @staticmethod
    def get_currency_for_country(country_code):
        """Determine currency based on country"""
        currency_map = {
            'NG': 'NGN',  # Nigeria
            'US': 'USD',  # United States
            'GH': 'GHS',  # Ghana
            'KE': 'KES',  # Kenya
            'ZA': 'ZAR',  # South Africa
            'GB': 'GBP',  # United Kingdom
        }
        return currency_map.get(country_code, 'USD')
    
    @staticmethod
    def get_exchange_rate(amount, from_currency='USD', to_currency='NGN'):
        """Convert amount between currencies (simplified)"""
        # In production, use real-time exchange rate API
        rates = {
            'USD_to_NGN': 1550,
            'NGN_to_USD': 0.00065,
        }
        
        if from_currency == to_currency:
            return amount
        
        rate_key = f"{from_currency}_to_{to_currency}"
        rate = rates.get(rate_key, 1)
        return round(amount * rate, 2)
    
    @staticmethod
    def detect_country(request):
        """Detect user's country from IP address"""
        # Try different methods to get country
        
        # Method 1: Cloudflare header (if using Cloudflare)
        country = request.META.get('HTTP_CF_IPCOUNTRY')
        if country:
            return country
        
        # Method 2: X-Forwarded-For header
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Method 3: Simple IP-based detection
        try:
            import requests as req
            response = req.get(f'https://ipapi.co/{ip}/country/', timeout=2)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        # Default to Nigeria for local testing
        return 'NG'
    
    @staticmethod
    def initialize_payment(order, request):
        """Initialize payment with Flutterwave"""
        
        # Check if Flutterwave keys are configured
        if not hasattr(settings, 'FLUTTERWAVE_PUBLIC_KEY') or not settings.FLUTTERWAVE_PUBLIC_KEY:
            return {
                'success': False,
                'error': 'Flutterwave payment gateway is not configured. Please contact support.'
            }
        
        # Detect user's country
        user_country = FlutterwavePayment.detect_country(request)
        currency = FlutterwavePayment.get_currency_for_country(user_country)
        
        # Convert amount if necessary
        if currency == 'NGN':
            amount = FlutterwavePayment.get_exchange_rate(
                float(order.total_amount), 
                'USD', 
                'NGN'
            )
        else:
            amount = float(order.total_amount)
        
        # Generate unique transaction reference
        tx_ref = f"ORDER-{order.id}-{uuid.uuid4().hex[:8]}"
        
        # Prepare payment data
        payment_data = {
            "tx_ref": tx_ref,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": request.build_absolute_uri(
                reverse('shop:payment_callback')
            ),
            "payment_options": "card,banktransfer,ussd,mobilemoney",
            "customer": {
                "email": order.email,
                "phonenumber": order.phone,
                "name": f"{order.first_name} {order.last_name}"
            },
            "customizations": {
                "title": "JejeHub Store",
                "description": f"Payment for Order #{order.id}",
                "logo": ""  # Add your logo URL here
            },
            "meta": {
                "order_id": order.id,
                "user_id": order.user.id if order.user else None,
                "original_amount": str(order.total_amount),
                "original_currency": "USD"
            }
        }
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{FlutterwavePayment.BASE_URL}/payments",
                json=payment_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                return {
                    'success': True,
                    'payment_link': result['data']['link'],
                    'tx_ref': tx_ref,
                    'currency': currency,
                    'amount': amount
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Payment initialization failed')
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Payment gateway timeout. Please try again.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    @staticmethod
    def verify_payment(transaction_id):
        """Verify payment status"""
        
        if not hasattr(settings, 'FLUTTERWAVE_SECRET_KEY') or not settings.FLUTTERWAVE_SECRET_KEY:
            return {
                'success': False,
                'error': 'Flutterwave is not configured'
            }
        
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{FlutterwavePayment.BASE_URL}/transactions/{transaction_id}/verify",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                data = result.get('data', {})
                return {
                    'success': True,
                    'status': data.get('status'),
                    'amount': data.get('amount'),
                    'currency': data.get('currency'),
                    'tx_ref': data.get('tx_ref'),
                    'customer': data.get('customer'),
                    'payment_type': data.get('payment_type')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Verification failed')
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Verification timeout'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }