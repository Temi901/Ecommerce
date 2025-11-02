# shop/templatetags/currency_filters.py
from django import template

register = template.Library()

# Exchange rates
USD_TO_NGN = 1550

@register.filter
def smart_currency(value, request=None):
    """
    Smart currency display based on user location
    For templates: {{ amount|smart_currency }}
    """
    try:
        usd_amount = float(value)
        
        # Default to NGN (since you're based in Nigeria)
        ngn_amount = usd_amount * USD_TO_NGN
        return f'₦{ngn_amount:,.2f}'
        
    except (ValueError, TypeError):
        return '₦0.00'


@register.filter
def naira(value):
    """
    Always display in Naira (convert from USD)
    Usage: {{ amount|naira }}
    """
    try:
        if value is None:
            return '₦0.00'
        ngn_amount = float(value) * USD_TO_NGN
        return f'₦{ngn_amount:,.2f}'
    except (ValueError, TypeError):
        return '₦0.00'


@register.filter
def dollar(value):
    """
    Always display in USD (no conversion)
    Usage: {{ amount|dollar }}
    """
    try:
        if value is None:
            return '$0.00'
        return f'${float(value):,.2f}'
    except (ValueError, TypeError):
        return '$0.00'


@register.filter
def auto_currency(value):
    """
    Auto-detect currency based on context
    Usage: {{ amount|auto_currency }}
    """
    try:
        usd_amount = float(value)
        # For now, default to Naira
        # You can make this smarter with middleware
        ngn_amount = usd_amount * USD_TO_NGN
        return f'₦{ngn_amount:,.2f}'
    except (ValueError, TypeError):
        return '₦0.00'


# NEW: Add this smart display price template tag
@register.simple_tag(takes_context=True)
def display_price(context, usd_price):
    """
    Smart price display based on user's currency
    Usage: {% display_price product.price %}
    """
    request = context.get('request')
    
    # Get currency from request (set by middleware)
    currency = getattr(request, 'currency', 'NGN')
    currency_symbol = getattr(request, 'currency_symbol', '₦')
    exchange_rate = getattr(request, 'exchange_rate', USD_TO_NGN)
    
    try:
        usd_amount = float(usd_price)
        converted_amount = usd_amount * exchange_rate
        return f'{currency_symbol}{converted_amount:,.2f}'
    except (ValueError, TypeError):
        return f'{currency_symbol}0.00'