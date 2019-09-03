# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from x_person.utils.x_person_init import x_person_init

from system_configuration.utils import init_database

if settings.PLATFORM_TYPE == 'AD':
    index_href = 'index_ad'
else:
    index_href = 'index_new'

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_user'),
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-user',
            },
        },

        {
            'name': _('x_user_manage'),
            'parent': _('x_user'),
            'href': 'user_list',
        },

        {
            'name': _('x_team_manage'),
            'parent': _('x_user'),
            'href': 'team_list',
            'CMS_OJ_SHOW': False,
        },

        {
            'name': _('x_organizational_structure_manage'),
            'parent': _('x_user'),
            'href': 'organization',
        },
        {
            'name': _('x_role_manage'),
            'parent': _('x_user'),
            'href': 'group_list',
        },
    ),
    'WEB_MENU': (
        # {
        #     'name': _('x_personal_center_oj'),
        #     'href': 'index_new',
        #     'icon': {'value': 'oj-icon oj-icon-E909 font25P'}
        # },
        # {
        #     'name': _('x_personal_center_ad'),
        #     'href': 'index_ad',
        #     'icon': {'value': 'oj-icon oj-icon-E909 font25P'}
        # },
        {
            'name': _('x_personal_center'),
            'parent': None,
            'href': index_href,
        },
        # {
        #     'name': _('x_growth_trajectory'),
        #     'parent':_("x_personal_center"),
        #     'href': 'person',
        #     'icon': {'value': 'oj-icon oj-icon-E91E font25P'}
        # },
        # {
        #     'name': _('x_my_profile'),
        #     'parent': _('x_personal_center'),
        #     'href': 'info',
        #     'icon': {'value': 'oj-icon oj-icon-E909 font25P'}
        # },
        # {
        #     'name': _('x_my_team'),
        #     'parent': _('x_personal_center'),
        #     'href': 'team',
        #     'icon': {'value': 'oj-icon oj-icon-E90A font25P'},
        #     'WEB_OJ_SHOW': False,
        # },
        # {
        #     'name': gettext('我的收藏'),
        #     'parent': '个人中心',
        #     'href': 'collect',
        #     'icon': {'value': 'oj-icon oj-icon-E90B font25P'}
        # },
        {
            'name': _('x_scoreboard'),
            'parent': _('x_practice'),
            'href': 'rank',
            'icon': {'value': 'oj-icon oj-icon-E928 font25P'},
            'WEB_AD_SHOW': False,
        },
    ),
    'SLUG': 'x_person',
    'RELY_ON': [],
    'LOGO_WHITE_LIST': ('gif', 'jpeg', 'jpg', 'bmp', 'png'),
}

IMPORT_STRINGS = ()

api_settings = APISettings('x_person', None, DEFAULTS, IMPORT_STRINGS)
init_database.register_init_function('x_person', x_person_init)
