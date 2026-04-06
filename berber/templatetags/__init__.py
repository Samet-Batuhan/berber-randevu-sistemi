from django import template
from berber.views import get_translation

register = template.Library()

@register.simple_tag
def trans(text, language='tr'):
    """Çeviri template tag'i"""
    return get_translation(text, language)
