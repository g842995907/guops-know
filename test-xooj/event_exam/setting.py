# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

from event.models import Event
from event.setting import api_settings as base_api_settings
from event_exam.utils.event_exam_init import event_exam_init
from system_configuration.utils import init_database

base_api_settings.EVENT_TYPES.append(Event.Type.EXAM)

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_exam'),
            'parent': _('x_contest'),
            'href': 'exam_list',
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_exam'),
            'parent': _('x_contest'),
            'href': 'list_new',
            'icon': {'value': 'oj-icon oj-icon-E905 font25P'}
        },
    ),
    'SLUG': 'event_exam',
    'RELY_ON': [
    ],
    'EVENT_TYPE': Event.Type.EXAM,
}

IMPORT_STRINGS = ()

api_settings = APISettings('event_exam', None, DEFAULTS, IMPORT_STRINGS)
init_database.register_init_function('event_exam', event_exam_init)

from django.conf import settings

if settings.PLATFORM_TYPE == "OJ":
    web_menus = api_settings.WEB_MENU
    web_menus[0]['parent'] = None