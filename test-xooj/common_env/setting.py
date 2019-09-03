# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

from system_configuration.utils import init_database

from .models import StandardDevice
from . import common_env_init

_DEFAULT_DEVICE_LOGO_DIR = 'standard_device_logo/default_device_logo/blue/'

_BASE_IMAGES = (
    {
        'dis_name': 'windows-10',
        'name': 'XOJ-DEFAULT-windows-10',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_10,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'nla',
        'user': 'Administrator',
        'password': 'password',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-8',
        'name': 'XOJ-DEFAULT-windows-8',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_8,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'nla',
        'user': 'root',
        'password': 'password',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-7',
        'name': 'XOJ-DEFAULT-windows-7',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_7,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'nla',
        'user': 'Administrator',
        'password': 'password',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-xp',
        'name': 'XOJ-DEFAULT-windows-xp',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_XP,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'rdp',
        'user': 'Administrator',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-server-2012',
        'name': 'XOJ-DEFAULT-windows-server-2012',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'nla',
        'user': 'Administrator',
        'password': 'password_win2012',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-server-2008',
        'name': 'XOJ-DEFAULT-windows-server-2008',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'nla',
        'user': 'Administrator',
        'password': 'password_win2008',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-server-2003',
        'name': 'XOJ-DEFAULT-windows-server-2003',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2003,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'rdp',
        'user': 'Administrator',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'windows-server-2000',
        'name': 'XOJ-DEFAULT-windows-server-2000',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.WINDOWS,
        'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2000,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'rdp',
        'user': 'Administrator',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
    {
        'dis_name': 'ubuntu-16',
        'name': 'XOJ-DEFAULT-ubuntu-16',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.UBUNTU_16,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'ubuntu-12',
        'name': 'XOJ-DEFAULT-ubuntu-12',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.UBUNTU_12,
        'access_mode': 'ssh',
        'access_port': '22',
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
    {
        'dis_name': 'centos-7',
        'name': 'XOJ-DEFAULT-centos-7',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.CENTOS_7,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'centos-6',
        'name': 'XOJ-DEFAULT-centos-6',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.CENTOS_6,
        'access_mode': 'ssh',
        'access_port': '22',
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'centos-5',
        'name': 'XOJ-DEFAULT-centos-5',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.CENTOS_5,
        'access_mode': 'ssh',
        'access_port': '22',
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
    {
        'dis_name': 'kali-linux',
        'name': 'XOJ-DEFAULT-kali-linux',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.KALI_2,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'password',
        'flavor': 'm3.1c-2g-20g',
        'init_support': True,
    },
    {
        'dis_name': 'android',
        'name': 'XOJ-DEFAULT-android',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.ANDROID,
        'access_mode': 'console',
        'access_port': '',
        'user': '',
        'password': '',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
    {
        'dis_name': 'UbuntuKylin-18.04',
        'name': 'XOJ-DEFAULT-UbuntuKylin-18.04',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.UBUNTUKYLIN_18,
        'access_mode': 'rdp',
        'access_port': 3389,
        'security': 'rdp',
        'user': 'ubuntukylin',
        'password': 'kylin123',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'OpenSolaris-11',
        'name': 'XOJ-DEFAULT-OpenSolaris-11',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.OPENSOLARIS_11,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'root123',
        'flavor': 'm3.1c-1g-20g',
        'init_support': False,
    },
    {
        'dis_name': 'OpenSUSE-Leap-42.3',
        'name': 'XOJ-DEFAULT-OpenSUSE-Leap-42.3',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.OPENSUSE_LEAP_42,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'root',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'debian-9.5',
        'name': 'XOJ-DEFAULT-debian-9.5.0',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.DEBIAN_9,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'debian',
        'password': 'debian',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'deepofix',
        'name': 'XOJ-DEFAULT-deepofix',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.DEEPOFIX,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'root',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
    {
        'dis_name': 'redhat-7',
        'name': 'XOJ-DEFAULT-redhat-7',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.REDHAT_7,
        'access_mode': 'ssh',
        'access_port': 22,
        'user': 'root',
        'password': 'password',
        'flavor': 'm2.1c-1g-10g',
        'init_support': True,
    },
    {
        'dis_name': 'backtrack-5',
        'name': 'XOJ-DEFAULT-backtrack-5',
        'image_type': StandardDevice.ImageType.VM,
        'system_type': StandardDevice.SystemType.LINUX,
        'system_sub_type': StandardDevice.SystemSubType.KALI_2,
        'access_mode': 'console',
        'access_port': '',
        'user': 'root',
        'password': 'toor',
        'flavor': 'm2.1c-1g-10g',
        'init_support': False,
    },
)

_FLAVOR_INFO = [
    ('m1.1c-0.5g-8g', _('x_m1.1c-0.5g-8g')),
    ('m1.1c-1g-8g', _('x_m1.1c-1g-8g')),
    ('m2.1c-0.5g-10g', _('x_m2.1c-0.5g-10g')),
    ('m2.1c-1g-10g', _('x_m2.1c-1g-10g')),
    ('m2.2c-2g-10g', _('x_m2.2c-2g-10g')),
    ('m2.2c-4g-10g', _('x_m2.2c-4g-10g')),
    ('m3.1c-1g-20g', _('x_m3.1c-1g-20g')),
    ('m3.1c-2g-20g', _('x_m3.1c-2g-20g')),
    ('m3.2c-4g-20g', _('x_m3.2c-4g-20g')),
    ('m3.4c-4g-20g', _('x_m3.4c-4g-20g')),
    ('m4.1c-1g-40g', _('x_m4.1c-1g-40g')),
    ('m4.2c-2g-40g', _('x_m4.2c-2g-40g')),
    ('m4.4c-4g-40g', _('x_m4.4c-4g-40g')),
    ('m4.4c-8g-40g', _('x_m4.4c-8g-40g')),
    ('m5.4c-4g-80g', _('x_m5.4c-4g-80g')),
    ('m5.4c-8g-80g', _('x_m5.4c-8g-80g')),
]

_FLAVORS = [flavor for flavor, text in _FLAVOR_INFO]

_DISK_FORMAT_INFO = [
    ('qcow2', _('x_qcow2')),
    ('vmdk', _('x_vmdk')),
    ('docker',_('x_docker_image')),
    # ('vhd', _('x_vhd')),
    ('vdi', _('x_vdi')),
    # ('ami', _('x_ami')),
    # ('ari', _('x_ari')),
    # ('iso', _('x_iso')),
    # ('ova', _('x_ova')),
    ('raw', _('x_origin')),
]

_DISK_CONTROLLER_INFO = [
    ('', _('x_none')),
    ('ide', _('ide')),
    ('virtio', _('virtio')),
    ('scsi', _('scsi')),
    ('uml', _('uml')),
    ('xen', _('xen')),
    ('usb', _('usb')),
]

_VIRTUAL_NETWORK_INTERFACE_DEVICE_INFO = [
    ('', _('x_none')),
    ('rtl8139', _('rtl8139')),
    ('virtio', _('virtio')),
    ('e1000', _('e1000')),
    ('ne2k_pci', _('ne2k_pci')),
    ('pcnet', _('pcnet')),
]

_VIDEO_IMAGE_DRIVER_INFO = [
    ('', _('x_none')),
    ('vga', _('vga')),
    ('cirrus', _('cirrus')),
    ('vmvga', _('vmvga')),
    ('xen', _('xen')),
    ('qxl', _('qxl')),
]


DEFAULTS = {
    'MENU': (
        {
            'name': _('x_env'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-globe',
            },
        },
        {
            'name': _('x_system_operation_maintenance'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-wrench',
            },
        },
        {
            'name': _('x_scene_management'),
            'parent': _('x_env'),
            'href': 'env_list',
        },
        # {
        #     'name': _('x_env_attacker_management'),
        #     'parent': _('x_env'),
        #     'href': 'env_attacker_list',
        # },
        {
            'name': _('x_target_management'),
            'parent': _('x_env'),
            'href': 'standard_device_list',
        },
        {
            'name': _('x_scene_instance'),
            'parent': _('x_system_operation_maintenance'),
            'href': 'active_env_list',
        },

    ),
    'WEB_MENU': (
    ),
    'SLUG': 'common_env',
    'RELY_ON': [
    ],
    'BASE_IMAGE': {image['name']: image for image in _BASE_IMAGES},
    'BASE_IMAGES': [image['name'] for image in _BASE_IMAGES],
    'BASE_IMAGE_TYPE': {image['name']: image['image_type'] for image in _BASE_IMAGES},
    'FLAVORS': _FLAVORS,
    'FLAVOR_INFO': _FLAVOR_INFO,
    'DISK_FORMAT_INFO': _DISK_FORMAT_INFO,
    'DISK_CONTROLLER_INFO': _DISK_CONTROLLER_INFO,
    'VIRTUAL_NETWORK_INTERFACE_DEVICE_INFO': _VIRTUAL_NETWORK_INTERFACE_DEVICE_INFO,
    'VIDEO_IMAGE_DRIVER_INFO': _VIDEO_IMAGE_DRIVER_INFO,

    # 环境配置文件名称
    'CONFIG_FILE_NAME': 'config.json',

    # 环境文件解压路径
    'EXTRACT_PATH': os.path.join(settings.BASE_DIR, 'common_env/media/env_files'),

    # 环境数量限制，目前是计算的环境数量而不是机器数量，待优化
    # 所有使用环境的地方独立判断
    'ALL_ENV_COUNT': 100,
    # 个人环境数量限制
    'PERSON_ENV_COUNT': 100,

    # 标靶默认logo目录
    'DEFAULT_DEVICE_LOGO_DIR': _DEFAULT_DEVICE_LOGO_DIR,
    'FULL_DEFAULT_DEVICE_LOGO_DIR': os.path.join(settings.MEDIA_ROOT, _DEFAULT_DEVICE_LOGO_DIR),

    # 场景网络网段
    'ENV_SUBNET_SEG': ['172.19'],

    # 环境创建完成回调函数集合，(当前创建快照时需要以继续创建快照)
    'ENV_CREATED_CALLBACKS': set(),

    # 环境创建错误回调函数集合
    'ENV_ERROR_CALLBACKS': set(),

    # 最大的flag数量，用以初始化创建快照时的默认flags参数，如果flags数量太小解析脚本可能出错
    'MAX_FLAG_COUNT': 100,

    # 获取正在使用的环境对象, 通知使用，各个实现的地方需提供方法， 返回对应的通知内容
    'GET_USING_ENV_OBJECTS_FUNCS': set(),

    # 获取忽略的个人环境数量
    'GET_IGNORED_USING_ENV_COUNT_FUNCS': set(),

    # 创建的网络，路由，虚拟机等资源的组名，用以区分
    'BASE_GROUP_NAME': 'XOJ_ENV',

    # 获取环境反向引用来源
    'GET_ENV_TARGET_FUNCS': set(),

    'SERVER_CREATE_POOL_LIMIT': 1,

    'WINDOWS_BASE_DIR': 'C:\\Users\\Public',

    'LINUX_BASE_DIR': '/tmp/tmp_installers',

    'INSTALLERS': [{
        'name': '迅雷',
        'resources': [{
            'version': '1.0.0',
            'file': 'env_installers/thunder-win7.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': '微信',
        'resources': [{
            'version': '1.0.0',
            'file': 'env_installers/WeChatSetup_sib.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': 'WPS',
        'resources': [{
            'version': '1.0.0',
            'file': 'env_installers/W.P.S-win7.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': 'Navicat',
        'resources': [{
            'version': '1.0.0',
            'file': 'env_installers/win7-navicat.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': 'Xshell',
        'resources': [{
            'version': '1.0.0',
            'file': 'env_installers/xshell5_wm2_sib.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': 'FoxitReader',
        'resources': [{
            'version': '9.2.0',
            'file': 'env_installers/foxit_FoxitReader_CHS_9.2.0.357911_sib.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }, {
        'name': 'Foxmail',
        'resources': [{
            'version': '7.2.9',
            'file': 'env_installers/FoxmailSetup_7.2.9.1161_sib.exe',
            'platforms': [StandardDevice.SystemSubType.WINDOWS_7],
            'install_script': '',
        }],
    }],

    'MAX_DOCKER_BLOCK_SECONDS': 20,

    'DEFAULT_DOCKER_NETWORK': "default_docker_network",
    'DOCKER_HOSTS': ['127.0.0.1'],
}

IMPORT_STRINGS = ()

api_settings = APISettings('common_env', None, DEFAULTS, IMPORT_STRINGS)

init_database.register_init_function('common_env', common_env_init)


from . import get_env_target_task
api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_task)
