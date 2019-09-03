# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_occupational_system'),
            'parent': _('x_course'),
            'href': 'occupation_list',
            'CMS_AD_SHOW': False,
        },

    ),
    'WEB_MENU': (
        # {
        #     'name': _('x_course'),
        #     'parent': None,
        #     'href': 'list'
        # },
    ),
    'SLUG': 'course_occupation',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()
api_settings = APISettings('course_occupation', None, DEFAULTS, IMPORT_STRINGS)
# init_database.register_init_function('course_occupation', system_configuration_init)
