from django import template
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
