# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_experiment'),
            'parent': _('x_practice_library'),
            'href': 'experiments',
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_experiment'),
            'parent': _('x_practice'),
            'href': 'list',
            'icon': {'value': 'oj-icon oj-icon-E923 font25P'}
        },
    ),
    'SLUG': 'experiment',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('experiment', None, DEFAULTS, IMPORT_STRINGS)
