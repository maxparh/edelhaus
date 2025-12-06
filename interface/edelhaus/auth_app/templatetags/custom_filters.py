from django import template

register = template.Library()

@register.filter
def format_currency(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".") + " ₽"
    except (ValueError, TypeError, AttributeError):
        return value