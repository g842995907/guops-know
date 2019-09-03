# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

from practice import api as practice_api
from practice_theory import api
from practice_theory.utils.practice_theory_init import practice_theory_init
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_theory'),
            'parent': _('x_practice_library'),
            'href': 'task_list',
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_theory'),
            'parent': _('x_practice'),
            'href': 'list',
            'icon': {'value': 'oj-icon oj-icon-E916 font25P'}
        },
    ),
    'SLUG': 'practice_theory',
    'RELY_ON': [],
    'WEB_AD_SHOW':False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_theory', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
    u'移动安全',
    u'网络基础知识',
    u'密码学基础',
    u'接入安全',
    u'主机安全',
    u'网络安全',
    u'办公安全',
    u'应用安全',
    u'数据库安全',
    u'云安全',
    u'安全服务',
    u'法律法规',
    u'安全防护',
    u'安全运维',
    u'安全工具',
    u'其他',
]

practice_api.register(practice_api.PRACTICE_TYPE_THEORY, categorys, api.TheoryPractice)

init_database.register_init_function('practice_theory', practice_theory_init)
