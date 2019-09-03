# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_cloud_management'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-group',
            },
            'CMS_AD_SHOW': False,
            'CMS_OJ_SHOW': False,
            'CMS_ALL_SHOW': False,
        },
        {
            'name': _('x_bureau_management'),
            'parent': _('x_cloud_management'),
            'href': 'department',
            'CMS_AD_SHOW': False,
            'CMS_OJ_SHOW': False,
            'CMS_ALL_SHOW': False,
        },
        {
            'name': _('x_version_management'),
            'parent': _('x_cloud_management'),
            'href': 'update',
            'CMS_AD_SHOW': False,
            'CMS_OJ_SHOW': False,
            'CMS_ALL_SHOW': False,
        },
    ),
    'WEB_MENU': (

    ),
    'SLUG': 'common_cloud',
    'RELY_ON': [
    ],
    'USE_SAME_KEY':True,
    'CLOUD_CENTER':"127.0.0.1:8000",
    'TENANT':''
}

IMPORT_STRINGS = ()

api_settings = APISettings('COMMON_CLOUD', None, DEFAULTS, IMPORT_STRINGS)
