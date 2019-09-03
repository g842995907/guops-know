# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
    ),
    'WEB_MENU': (
        {
            'name': _('x_vulnerability'),
            'parent': None,
            'href': 'global',
            'icon': {'value': 'oj-icon oj-icon-E90D font25P'}
        },
    ),
    'SLUG': 'x_vulns',
    'RELY_ON': [
    ],
    'SERVER': 'http://10.10.49.253:8082',
    'LIST_URL': '/api/vuln_list',
    'DETAIL_URL': '/api/vuln_detail',
    'GLOBAL_RISK': '/api/risk',
    'GLOBAL_TYPE': '/api/type_statistics',
    'GLOBAL_TIME': '/api/time_distribution',
}

IMPORT_STRINGS = ()

api_settings = APISettings('x_vulns', None, DEFAULTS, IMPORT_STRINGS)
