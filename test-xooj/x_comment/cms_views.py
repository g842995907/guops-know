# coding=utf-8
from __future__ import unicode_literals
import logging

from django.shortcuts import render
from x_comment.setting import api_settings
from django.conf import settings

LOG = logging.getLogger(__name__)
slug = api_settings.SLUG
from django.utils.translation import ugettext_lazy as _


# @find_menu(slug)
def comment_list(request):
    pt = settings.PLATFORM_TYPE
    if pt == "OJ":
        type_list = {"0": _('x_course'), "2": _('x_real_vuln'), "3": _('x_exercise')}
    elif pt == "ALL":
        type_list = {"0": _('x_course'), "1": _('x_tool'), "2": _('x_real_vuln'), "3": _('x_exercise')}
    else:
        type_list = {"1": _('x_tool')}
    context = {
        'type_list': type_list,
    }
    return render(request, 'x_comment/cms/comment_list.html', context)
