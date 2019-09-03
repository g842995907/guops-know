# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings
from common_framework.utils.x_logger import load_log_config
from system_configuration.models import SystemConfiguration
from system_configuration.utils import init_database
from system_configuration.utils.loger import logset
from system_configuration.utils.system_configuration_init import system_configuration_init

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_system_management'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-gear',
            },
        },
        {
            'name': _('x_system_configuration'),
            'parent': _('x_system_management'),
            'href': 'system_configuration',
        },
        {
            'name': _('x_authorization_date'),
            'parent': _('x_system_management'),
            'href': 'license',
        },
        {
            'name': _('x_cluster_status'),
            'parent': _('x_system_operation_maintenance'),
            'href': 'operation_services',
        },
        # {
        #     'name': _('备份与恢复'),
        #     'parent': _('系统管理'),
        #     'href': 'backup',
        # },
        {
            'name': _('x_run_log_manage'),
            'parent': _('x_system_management'),
            'href': 'run_log',
        },
        {
            'name': _('x_shenji_log'),
            'parent': _('x_system_management'),
            'href': 'log',
        },
        {
            'name': _('x_sys_notice'),
            'parent': None,
            'href': 'sys_notice_list',
            'icon':{
                'style': 'font awesonme',
                'value': 'fa fa-commenting-o',
            }
        }
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'system_configuration',
    'RELY_ON': [
    ],
    'SSH_HOST_IP': '10.10.50.249',
    'SSH_USERNAME': 'cyberpeace',
    'LOG_ZIP_PASSWORD' : 'DrC8YARLCK4dI8h&6@H&UJU&YplfAyD',
    'SHOW_NOTICE': False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('system_configuration', None, DEFAULTS, IMPORT_STRINGS)
init_database.register_init_function('system_configuration', system_configuration_init)

