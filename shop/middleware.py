from django.utils.deprecation import MiddlewareMixin

class CurrencyMiddleware(MiddlewareMixin):
    """
    Middleware to detect user's currency preference
    """
    
    def process_request(self, request):
        # Check if user has manually selected currency
        if 'currency' in request.session:
            request.currency = request.session['currency']
            return
        
        # Try to detect from IP
        country = self.detect_country(request)
        
        if country == 'NG':
            request.currency = 'NGN'
            request.currency_symbol = '₦'
            request.exchange_rate = 1550
        elif country == 'US':
            request.currency = 'USD'
            request.currency_symbol = '$'
            request.exchange_rate = 1
        else:
            # Default to NGN for other countries
            request.currency = 'NGN'
            request.currency_symbol = '₦'
            request.exchange_rate = 1550
    
    def detect_country(self, request):
        """Detect country from IP"""
        # Method 1: Cloudflare
        country = request.META.get('HTTP_CF_IPCOUNTRY')
        if country:
            return country
        
        # Method 2: Get IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # For local development
        if ip in ['127.0.0.1', 'localhost']:
            return 'NG'  # Default to Nigeria for testing
        
        # Method 3: IP API (cached)
        try:
            import requests
            response = requests.get(f'https://ipapi.co/{ip}/country/', timeout=2)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        return 'NG'  # Default to Nigeria
