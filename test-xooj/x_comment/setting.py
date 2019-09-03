# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_cloud_exchange'),
            'parent': None,
            'href': 'comments',
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-comments',
            },
        },
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'x_comment',
    'RELY_ON': [
    ],
}

IMPORT_STRINGS = ()

api_settings = APISettings('x_comment', None, DEFAULTS, IMPORT_STRINGS)
