# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.conf import settings

from common_framework.x_setting.settings import APISettings


_GUACAMOLE_RECORDING_DIR_NAME = 'guac_recording'

DEFAULTS = {
    'MENU': (
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'common_remote',
    'RELY_ON': [
    ],

    'DATABASE': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'guacamole_db',
        'USER': 'guacamole_user',
        'PASSWORD': 'guacamole_pass',
        'HOST': '127.0.0.1',
        'PORT': '3306'
    },

    'OJ_SERVER': {
        'host_ip': '127.0.0.1',
        'ssh_username': 'root',
        'ssh_password': '123',
    },

    'GUACAMOLE_SERVERS': [
        {
            'host_ip': '127.0.0.1',
            'server': 'http://127.0.0.1:8080',
            'public_server': 'http://127.0.0.1:8080',
            'ssh_username': 'root',
            'ssh_password': '123',
        }
    ],

    'GUACAMOLE_API_PATH_TOKENS': '/tokens',

    'GUACAMOLE_API_PATH_ACTIVE_SESSIONS': '/session/data/mysql/activeConnections',

    'GUACAMOLE_API_PATH_SHARE_ACTIVE_SESSION': '/session/tunnels/{session_id}/activeConnection/sharingCredentials/{sharing_profile_id}',

    'GUACAMOLE_PATH_SHARED_ACTIVE_SESSION': '{server}/guacamole/#/client/{client_name}?key={key}',

    'GUACAMOLE_CONNECTION_URL': '{server}/guacamole/#/client/{client_name}',

    # 用于设置登录信息cookie路径(相对路径) 废弃
    'GUACAMOLE_COOKIE_PATH': '/guacamole',


    # 内部调用guacamole api
    'GUACAMOLE_API_URL_PREFIX': '{server}/guacamole/api',

    'GUACADMIN_USER': {
        'id': 0,
        'username': 'guacadmin',
        'password': 'guacadmin',
    },

    'GUACADMIN_MAX_CONNECTIONS': None,

    # 每个连接最大活动连接数设为None或1, 如果多个会话，监控很麻烦
    'GUACADMIN_MAX_CONNECTIONS_PER_USER': None,

    # rdp共享文件夹
    'GUACDRIVE_PATH': '/tmp/guacdrive',

    # 视频目录
    'RECORDING_SOURCE_PATH': os.path.join('/tmp', _GUACAMOLE_RECORDING_DIR_NAME),
    # 视频录制目录
    'RECORDING_PATH': os.path.join(settings.MEDIA_ROOT, _GUACAMOLE_RECORDING_DIR_NAME),
    # 视频转换回调
    'RECORDING_CONVERT_CALLBACK': {},
}

IMPORT_STRINGS = ()

api_settings = APISettings('common_remote', None, DEFAULTS, IMPORT_STRINGS)


settings.DATABASES['guacamole'] = api_settings.DATABASE
