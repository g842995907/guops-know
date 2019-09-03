# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import gettext

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        # {
        #     'name': gettext('用户笔记'),
        #     'parent': None,
        #     'href': 'notes',
        #     'icon': {
        #         'style': 'font awesonme',
        #         'value': 'fa fa-file-text',
        #     },
        # },
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'x_note',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('x_note', None, DEFAULTS, IMPORT_STRINGS)
