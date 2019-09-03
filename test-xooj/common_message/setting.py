# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import gettext

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
    ),
    'WEB_MENU': (
    ),
    'SLUG':'message',
    'RELY_ON': [],
}

IMPORT_STRINGS = ()

api_settings = APISettings('message', None, DEFAULTS, IMPORT_STRINGS)

