from django import template
import locale

register = template.Library()

@register.filter
def currency(value):
    try:
        # Set locale to Spanish for proper formatting
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        return locale.currency(value, grouping=True)
    except:
        # Fallback if locale not available
        return f"${value:,.2f}"