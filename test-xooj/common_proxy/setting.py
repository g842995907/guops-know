# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from common_framework.x_setting.settings import APISettings

DEFAULTS = {
    'MENU': (

    ),
    'WEB_MENU': (
    ),
    'SLUG': 'proxy',
    'RELY_ON': [],

    # nginx配置中, tcp代理配置文件路径
    'NGX_CONF_PATH': '/usr/local/nginx/conf/tcp.d/',
    # 重启nginx命令
    'NGX_REBOOT_CMD': '/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/xoj.conf -s reload',
    # 启动nginx命令
    'NGX_START_CMD': '/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/xoj.conf',
    # nginx代理随机端口选择范围
    'PROXY_START_PORT': 20000,
    'PROXY_END_PORT': 30000,
    'PROXY_IP': '127.0.0.1',
    'SWITCH':False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('common_proxy', None, DEFAULTS, IMPORT_STRINGS)
