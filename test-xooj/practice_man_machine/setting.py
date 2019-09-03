# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from practice import api as practice_api
from practice_man_machine import api
from practice_man_machine.utils.practice_man_machine_init import practice_man_machine_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        # {
        #     'name': _('x_man_machine'),
        #     'parent': _('x_practice'),
        #     'href': 'task_list',
        # },
    ),
    'WEB_MENU': (
        # {
        #     'name': _('x_man_machine'),
        #     'parent': _('x_practice'),
        #     'href': 'list',
        #     'icon': {'value': 'oj-icon oj-icon-E903 font25P'}
        # },
    ),
    'SLUG': 'practice_man_machine',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_man_machine', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
    u"web攻防",
    u"二进制攻防",
    u"其他"
]

# practice_api.register(practice_api.PRACTICE_TYPE_MAN_MACHINE, categorys, api.ManMachinePractice)
init_database.register_init_function('practice_man_machine', practice_man_machine_init)

from common_env.setting import api_settings as common_env_api_settings
from . import get_using_env_tasks, get_env_target_task

common_env_api_settings.GET_USING_ENV_OBJECTS_FUNCS.add(get_using_env_tasks)
common_env_api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_task)