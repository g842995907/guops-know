# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_toolbox'),
            'parent': None,
            'href': 'tools',
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-briefcase',
            },
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_toolbox'),
            'parent': None,
            'href': 'list',
            'icon': {'value': 'oj-icon oj-icon-E90D font25P'}
        },
    ),
    'SLUG': 'x_tools',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('x_tools', None, DEFAULTS, IMPORT_STRINGS)
