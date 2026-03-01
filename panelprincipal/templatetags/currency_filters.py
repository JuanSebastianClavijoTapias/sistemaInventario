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

@register.filter
def formato_pesos(value):
    """Formatea un número como pesos colombianos con separador de miles"""
    try:
        value = float(value)
        # Formato con separador de miles (punto) sin decimales
        formatted = '{:,.0f}'.format(value)
        # Cambiar comas por puntos para formato colombiano
        formatted = formatted.replace(',', '.')
        return f'${formatted}'
    except (ValueError, TypeError):
        return f'${value}'

@register.filter
def numero_limpio(value):
    """Devuelve el número sin formato, solo dígitos (para usar en JavaScript)"""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0