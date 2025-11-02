def search_query(request):
    """Make search query available to all templates"""
    return {
        'search_query': request.GET.get('q', '')
    }
def currency_context(request):
    """
    Add currency info to all templates
    """
    currency = getattr(request, 'currency', 'NGN')
    currency_symbol = getattr(request, 'currency_symbol', '₦')
    exchange_rate = getattr(request, 'exchange_rate', 1550)
    
    return {
        'user_currency': currency,
        'currency_symbol': currency_symbol,
        'exchange_rate': exchange_rate,
    }