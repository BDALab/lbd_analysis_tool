from django import template


# Prepare the template registration
register = template.Library()


@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    """Returns a relative URL with extra attributes"""

    # Prepare the url
    url = f'?{field_name}={value}'

    # Handle the urlencoded attributes
    if urlencode:

        # Prepare the attributes
        query_string = filter(lambda p: p.split('=')[0] != field_name, urlencode.split('&'))
        query_string = '&'.join(query_string)

        # Join the attributes
        url = f'{url}&{query_string}'

    # Return the relative URL
    return url
