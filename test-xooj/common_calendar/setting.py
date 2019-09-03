# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from common_calendar.api import calendar_init
from common_framework.x_setting.settings import APISettings
from system_configuration.utils import init_database

DEFAULTS = {
    'MENU': (

    ),
    'WEB_MENU': (
    ),
    'SLUG':'calendar',
    'RELY_ON': [],
}

IMPORT_STRINGS = ()

api_settings = APISettings('calendar', None, DEFAULTS, IMPORT_STRINGS)
init_database.register_init_function('calendar', calendar_init)

