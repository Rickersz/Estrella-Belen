from django import template
from django.utils.safestring import mark_safe

register = template.Library()   # for registering custom template tags and filters

@register.filter(name='checkbox')
def checkbox(value):
    """
    Converts a boolean value to a checkbox representation.
    Usage in template: {{ value|checkbox }}
    """
    if value:
        return mark_safe('<input type="checkbox" checked disabled>')  # Checked checkbox
    else:
        return mark_safe('<input type="checkbox" disabled>')