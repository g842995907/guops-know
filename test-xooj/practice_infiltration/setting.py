# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from practice import api as practice_api
from practice_infiltration import api
from practice_infiltration.utils.practice_infiltration_init import practice_infiltration_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_infiltration'),
            'parent': _('x_practice_library'),
            'href': 'task_list',
            'CMS_OJ_SHOW': False,
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_infiltration'),
            'parent': _('x_practice'),
            'href': 'list',
            'icon': {'value': 'oj-icon oj-icon-E91F font25P'},
            'WEB_OJ_SHOW': False,
        },
    ),
    'SLUG': 'practice_infiltration',
    'RELY_ON': [
    ],
    'WEB_AD_SHOW':False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_infiltration', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
    u"Web",
    u"Pwn",
    u"Reverse",
    u"Mobile",
    u"Crypto",
    u"Misc",
    u"Code",
    u"Other"
]

practice_api.register(practice_api.PRACTICE_TYPE_INFILTRATION, categorys, api.InfiltrationPractice)
init_database.register_init_function('practice_infiltration', practice_infiltration_init)


from common_env.setting import api_settings as common_env_api_settings
from . import get_using_env_tasks, get_env_target_task
common_env_api_settings.GET_USING_ENV_OBJECTS_FUNCS.add(get_using_env_tasks)
common_env_api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_task)
