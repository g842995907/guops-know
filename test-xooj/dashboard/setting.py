# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_dashboard'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-dashboard',
            },
            'href': 'dashboard',
        },
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'dashboard',
    'RELY_ON': [
    ],
    # cpu ram disk 告警比例配置

    'ALARM_PERCENT': {
         'cpu_alarm_percent': 80,
         'ram_alarm_percent': 80,
         'disk_alarm_percent': 80,
    }

}

IMPORT_STRINGS = ()

api_settings = APISettings('dashboard', None, DEFAULTS, IMPORT_STRINGS)
