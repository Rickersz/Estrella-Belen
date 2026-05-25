from django import template

register = template.Library()   # for registering custom template tags and filters

@register.simple_tag(takes_context=True)        # register a simple tag that takes the template context
def is_active_menu(context, url_name):
    """
    Check if the given menu item is the active page.
    Usage in template: {% is_active 'menu_item_name' %}
    """

    ''' 
    # for static path matching
    request = context['request']               # get the current request from the context
    current_path = request.path                 # get the current path from the request
    return 'active show' if current_path.startswith(f'/{menu_item}/') else ''
    '''

    # for dynamic path matching
    current_url = context.request.resolver_match.url_name  # get the current URL name from the request context
    
    return 'active' if current_url == url_name else ''