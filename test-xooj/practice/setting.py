# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from practice.utils.practice_init import practice_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_practice_library'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-leaf',
            },
        },

        {
            'name': _('x_event_manage'),
            'parent': _('x_practice_library'),
            'href': 'event_list',
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_practice'),
            'parent': None,
        },
    ),
    'SLUG': 'practice',
    'RELY_ON': [
    ],
    'WEB_AD_SHOW': False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice', None, DEFAULTS, IMPORT_STRINGS)
init_database.register_init_function('practice', practice_init)

from common_env.setting import api_settings as common_env_api_settings
from . import get_ignored_using_env_count

common_env_api_settings.GET_IGNORED_USING_ENV_COUNT_FUNCS.add(get_ignored_using_env_count)
