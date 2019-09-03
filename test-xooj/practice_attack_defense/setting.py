# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.x_setting.settings import APISettings
from practice import api as practice_api
from practice_attack_defense import api
from practice_attack_defense.utils.practice_attack_defense_init import practice_attack_defense_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_ad_mode'),
            'parent': _('x_practice_library'),
            'href': 'task_list',
            'CMS_OJ_SHOW': False,
        },
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'practice_attack_defense',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_attack_defense', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
    u"Web",
    u"Pwn",
]

practice_api.register(practice_api.PRACTICE_TYPE_ATTACK_DEFENSE, categorys, api.AttackDefensePractice)
init_database.register_init_function('practice_attack_defense', practice_attack_defense_init)

from common_env.setting import api_settings as common_env_api_settings
from . import get_env_target_task
common_env_api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_task)