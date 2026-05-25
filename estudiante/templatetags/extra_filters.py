from django import template

register = template.Library()

@register.filter
def split(value, sep=None):
    """Split the string by given separator and return a list. If sep is None, split on whitespace."""
    if value is None:
        return []
    try:
        return value.split(sep)
    except Exception:
        return [value]
