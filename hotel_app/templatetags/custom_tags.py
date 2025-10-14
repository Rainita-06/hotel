from django import template

register = template.Library()

@register.filter
def get_attribute(obj, attr_name):
    """Return attribute of an object dynamically in templates"""
    return getattr(obj, attr_name, "")


@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0