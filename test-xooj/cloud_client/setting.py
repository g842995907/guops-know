# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_upgrade_management'),
            'parent': _('x_system_management'),
            'href': 'update',
        },
    ),
    'WEB_MENU': (

    ),
    'SLUG': 'cloud_client',
    'RELY_ON': [
    ],
    'update_zip':'23pZvWBBmlgRNDShLTWEieDsLjnHU6c0',
    'version_host':'version.cyberpeace.cn',
}

IMPORT_STRINGS = ()

api_settings = APISettings('CLOUD_CLIENT', None, DEFAULTS, IMPORT_STRINGS)
