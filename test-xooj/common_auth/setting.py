# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import gettext

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (),
    'WEB_MENU': (),
    'SLUG': 'auth',
    'RELY_ON': [],
    'OFFLINE_TIME': 300,
}

IMPORT_STRINGS = ()

api_settings = APISettings('AUTH', None, DEFAULTS, IMPORT_STRINGS)
