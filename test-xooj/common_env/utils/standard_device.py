# -*- coding: utf-8 -*-
import json
import logging

from common_remote.managers import RemoteManager
from common_env.handlers.local_lib import scene, proxy
from common_env.models import StandardDeviceEditServer


logger = logging.getLogger(__name__)


def delete_tmp_vm(tmp_vm, destroy=True):
    # 删机器
    if tmp_vm.tmp_vm_id:
        scene.vm.delete(tmp_vm.tmp_vm_id)
    if tmp_vm.tmp_docker_id:
        scene.docker.delete(tmp_vm.tmp_docker_id)

    # 删路由
    if tmp_vm.tmp_router_ids:
        tmp_router_ids = json.loads(tmp_vm.tmp_router_ids)
        for router_id in tmp_router_ids:
            scene.router.delete(router_id)

    # 删网络端口
    if tmp_vm.tmp_net_ports:
        tmp_net_ports = json.loads(tmp_vm.tmp_net_ports)
        for port_id in tmp_net_ports:
            try:
                scene.network.delete_port(port_id)
            except Exception as e:
                logger.error("delete tmp vm net ports error")

    # 删网络
    if tmp_vm.tmp_network_ids:
        tmp_network_ids = json.loads(tmp_vm.tmp_network_ids)
        for network_id in tmp_network_ids:
            scene.network.delete(network_id)

    # 删连接
    if tmp_vm.connection_id:
        try:
            RemoteManager().remove_connection(tmp_vm.connection_id)
        except Exception as e:
            logger.error('remove guacamole connection error: %s', e)
    # 删代理
    if tmp_vm.float_ip and tmp_vm.port and tmp_vm.proxy_port:
        try:
            proxy.delete_proxy(tmp_vm.float_ip, [tmp_vm.port])
        except:
            pass
    # 删记录
    if destroy:
        tmp_vm.delete()
    else:
        tmp_vm.status = StandardDeviceEditServer.Status.DELETED
        tmp_vm.save()
