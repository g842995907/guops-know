# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from practice import api as practice_api
from practice_real_vuln import api
from practice_real_vuln.utils.practice_real_vuln_init import practice_real_vuln_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_real_vuln'),
            'parent': _('x_practice_library'),
            'href': 'task_list',
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_real_vuln'),
            'parent': _('x_practice'),
            'href': 'list',
            'icon': {'value': 'oj-icon oj-icon-E901 font25P'}
        },
    ),
    'SLUG': 'practice_real_vuln',
    'RELY_ON': [
    ],
    'WEB_AD_SHOW':False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_real_vuln', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
    u"web漏洞",
    u"移动端漏洞",
    u"硬件漏洞",
    u"操作系统漏洞",
    u"射频漏洞",
    u"工控漏洞",
    u"其他漏洞",
]

practice_api.register(practice_api.PRACTICE_TYPE_REAL_VULN, categorys, api.RealVulnPractice)
init_database.register_init_function('practice_real_vuln', practice_real_vuln_init)


from common_env.setting import api_settings as common_env_api_settings
from . import get_using_env_tasks, get_env_target_task
common_env_api_settings.GET_USING_ENV_OBJECTS_FUNCS.add(get_using_env_tasks)
common_env_api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_task)