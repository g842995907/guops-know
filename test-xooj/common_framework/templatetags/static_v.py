# -*- coding: utf-8 -*-
import os
import hashlib

from django import template
from django.conf import settings
from django.templatetags.static import StaticNode, PrefixNode

register = template.Library()

class StaticVNode(StaticNode):

    def render(self, context):
        url = self.url(context)
        if self.varname is None:
            return get_url_with_version(url)
        context[self.varname] = url
        return ''


@register.tag('static_v')
def do_static_v(parser, token):
    return StaticVNode.handle_token(parser, token)


def static_v(path):
    return StaticVNode.handle_simple(path)

def get_url_with_version(url):
    for vdir in settings.STATIC_V_DIRS:
        file_path = os.path.join(vdir, url.lstrip('/'))
        if os.path.exists(file_path):
            modified_time = os.path.getmtime(file_path)
            modified_time = hashlib.md5(str(modified_time)).hexdigest()
            return '%s?%s' % (url, modified_time)
    return url