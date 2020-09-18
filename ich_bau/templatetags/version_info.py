﻿from django import template

register = template.Library()

@register.simple_tag(name='site_version_info')
def site_version_info():
    return 'v0.0031 at 18.09.2020'
