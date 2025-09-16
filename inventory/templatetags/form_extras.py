from django import template
from inventory.constants import CO_MANAGER_GROUP

register = template.Library()

@register.filter
def add_class(field, css):
    # If already rendered (SafeString), don't attempt to re-render
    if not hasattr(field, 'as_widget'):
        return field
    # Merge with any existing class on the widget
    try:
        existing = field.field.widget.attrs.get('class', '')
    except Exception:
        existing = ''
    classes = f"{existing} {css}".strip()
    return field.as_widget(attrs={'class': classes})

@register.filter(name='add_attr')
def add_attr(field, arg):
    """Usage: {{ field|add_attr:"list=categoriesList" }}"""
    try:
        key, value = arg.split('=', 1)
    except ValueError:
        return field
    # If this is already rendered HTML (SafeString), we can't call as_widget.
    # In that case, just return the field unchanged to avoid crashes.
    if not hasattr(field, 'as_widget'):
        return field
    return field.as_widget(attrs={key.strip(): value.strip()})

@register.filter(name='mask_digits')
def mask_digits(value):
    """Replace all digits in the rendered value with 'x'.
    Useful for masking monetary figures for non-admin viewers while preserving format.
    """
    try:
        s = f"{value}"
    except Exception:
        s = str(value)
    masked = ''.join('X' if ch.isdigit() else ch for ch in s)
    return masked

@register.filter(name='is_comanager')
def is_comanager(user):
    """Return True when the user belongs to the co-manager group."""
    try:
        auth = getattr(user, 'is_authenticated', False)
        if callable(auth):
            auth = auth()
        if not auth or not getattr(user, 'is_staff', False):
            return False
        return user.groups.filter(name=CO_MANAGER_GROUP).exists()
    except Exception:
        return False
