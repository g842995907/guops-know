from __future__ import unicode_literals

import socket

from common_scene.setting import api_settings

from common_proxy import nginx
from common_proxy.setting import api_settings as proxy_api_settings


__version__ = '1.1.1'


if proxy_api_settings.SWITCH:
    ip = socket.gethostbyname('controller')
    if ip:
        proxy_port = nginx.get_proxy(ip, api_settings.CONSOLE_PORT)
        if not proxy_port:
            proxy_port = nginx.add_proxy(ip, api_settings.CONSOLE_PORT, timeout=3600)
            nginx.restart_nginx()

        api_settings.CONSOLE_PROXY_PORT = proxy_port
