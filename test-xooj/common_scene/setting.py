from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        # {
        #     'name': _('x_openstack_api'),
        #     'parent': None,
        #     'icon': {
        #         'style': 'font awesonme',
        #         'value': 'fa fa-wrench',
        #     },
        # },
        {
            'name': _('x_instance_api'),
            'parent': _('x_system_operation_maintenance'),
            'href': 'instance_api_list',
        }, {
            'name': _('x_network_api'),
            'parent': _('x_system_operation_maintenance'),
            'href': 'network_api_list',
        },
        # {
        #     'name': _('x_image_api'),
        #     'parent': _('x_system_operation_maintenance'),
        #     'href': 'image_api_list',
        # },
        # {
        #     'name': _('x_firewall_api'),
        #     'parent': _('x_openstack_api'),
        #     'href': 'firewall_api_list',
        # },
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'common_scene',
    'RELY_ON': [

    ],

    "OS_AUTH": {
        'auth_url': 'http://controller:35357/v3/',
        'username': 'admin',
        'password': 'ADMIN_PASS',
        'project_name': 'admin',
        'project_id': '',
        'user_domain_id': 'default',
        'project_domain_id': 'default'
    },

    # for complex scene
    "COMPLEX_MISC": {
        'external_net': "8a4a30e6-3ec0-4f44-9945-00b341ec9940",
        'linux_flavor': "m2.1c-1g-10g",
        'windows_flavor': "m4.4c-4g-40g",
        'security_groups': [],
        'keypairs': "",
        'ftp_path': "/home/ftp",
        'controller_root_pwd': "123456",
        'clean_env': False,
        'subnet_seg': ['172.19'],
        'ad_subnet_seg': {
            'cidr': '172.{}.{}.{}/24',
            'range': [16, 100]
        },
        'cpu_allocation_ratio': 4,
        'ram_allocation_ratio': 1.0,
        'disk_allocation_ratio': 2.0,
        'glance_image_dir': "/var/lib/glance/images/",
        'dns_nameservers': ['114.114.114.114'],
        'memcache_host': ['127.0.0.1:11211'],
        'report_vm_status': '%s/common_env/update_vm_status/' % settings.SERVER_HOST,
        'report_template_vm_status': '%s/common_env/api/standard_devices/{}/tmp_vm_running/' % settings.SERVER_HOST,
    },

    'CONSOLE_PROTOCOL': 'vnc',
    'CONSOLE_PORT': 6080,
    'CONSOLE_PROXY_PORT': 6080,

    # image and instance don't show
    "DONT_SHOW": {
        'instance_list': ["OJ-3.1", 'OJ'],
        'image_list': ["OJ-117", 'OJ-Standard', 'OJ'],
    },

    # controller httpd  port
    'CONTROLLER_HTTPD_PORT': 80,
}

IMPORT_STRINGS = ()

api_settings = APISettings('scene', None, DEFAULTS, IMPORT_STRINGS)
