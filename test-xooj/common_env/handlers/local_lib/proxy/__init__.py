import logging

from common_proxy import nginx
from common_proxy.setting import api_settings

logger = logging.getLogger(__name__)

PROXY_IP = api_settings.PROXY_IP
PROXY_SWITCH = api_settings.SWITCH


def create_proxy(ip, ports, timeout=300):
    if isinstance(ports, (tuple, set, list)):
        return nginx.add_new_proxy(ip, ports, timeout=timeout)
    else:
        return nginx.add_proxy(ip, ports, timeout=timeout)


def delete_proxy(ip, ports):
    logger.debug("---------------------------")
    if not isinstance(ports, (tuple, set, list)):
        ports = (ports,)

    for port in ports:
        logger.debug("delete proxy %s:%s START", ip, port)
        nginx.delete_proxy(ip, port)
        logger.debug("delete proxy %s:%s END", ip, port)


def restart_proxy():
    nginx.restart_nginx()
