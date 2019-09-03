# -*- coding: utf-8 -*-
import copy
import os
import logging
import random
import time
import uuid
import socket
import time

from common_framework.utils.cmd import exe_cmd
from common_framework.utils.network import ping
from common_proxy.nginx import get_new_valid_port
from common_scene.complex.views import BaseScene, states, ATTEMPTS
from common_env.setting import api_settings

from ..base.base import Resource
from .utils import str_filter


logger = logging.getLogger(__name__)


class Docker(Resource):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def get(self, container_id, convert_host_ip=True):
        container = self.operator.get_container(container_id, convert_host_ip)
        container.id = container.uuid
        return container

    def create(self, **kwargs):
        params = self.load_create_params(**kwargs)
        container = self.send_create(**params)
        container = self.check_create(container, **params)
        return container

    def send_create(self, **params):
        container = self.operator.scene_send_create_container(**params)
        container.id = container.uuid
        return container

    def check_create(self, container, **params):
        container = self.operator.scene_check_create_container(container, **params)
        container.id = container.uuid
        return container

    def create_qos(self, name, container_id=None, network_id=None, rule=None):
        container = self.get(container_id) if container_id else None
        return self.operator.scene_create_qos(name=name, container=container, network_id=network_id, rule=rule)

    def update(self, container_id, **kwargs):
        float_ip = kwargs.get('float_ip')
        if float_ip:
            self.operator.bind_fip(float_ip, port=kwargs.get('fip_port'), instance=self.get(container_id))

    def delete(self, container_id, sync=True, local=False, host=None):
        if local:
            exe_cmd('{docker} stop {name} && {docker} rm {name}'.format(
                docker=local_docker_cmd(host),
                name=container_id,
            ))
        else:
            container = self.get(container_id)
            if container.status == states['RUNNING']:
                self.stop(container_id)
                attempts = ATTEMPTS
                while 1:
                    if attempts <= 0:
                        self.operator.delete_container(container_id, sync, force=False)
                        break
                    container = self.get(container_id)
                    if container.status != states['RUNNING']:
                        self.operator.delete_container(container_id, sync, force=False)
                        break
                    attempts -= 1
                    time.sleep(1)
            else:
                self.operator.delete_container(container_id, sync, force=False)

    def pause(self, container_id, local=False, host=None):
        if local:
            exe_cmd('{docker} pause {name}'.format(docker=local_docker_cmd(host), name=container_id))
        else:
            self.operator.pause_container(container_id)

    def unpause(self, container_id, local=False, host=None):
        if local:
            exe_cmd('{docker} unpause {name}'.format(docker=local_docker_cmd(host), name=container_id))
        else:
            self.operator.unpause_container(container_id)

    def start(self, container_id, local=False, host=None):
        if local:
            exe_cmd('{docker} start {name}'.format(docker=local_docker_cmd(host), name=container_id))
        else:
            self.operator.start_container(container_id)

    def stop(self, container_id, local=False, host=None):
        if local:
            exe_cmd('{docker} stop {name}'.format(docker=local_docker_cmd(host), name=container_id))
        else:
            self.operator.stop_container(container_id)

    def restart(self, container_id, local=False, host=None):
        if local:
            exe_cmd('{docker} restart {name}'.format(docker=local_docker_cmd(host), name=container_id))
        else:
            self.operator.restart_container(container_id)

    def cp(self, container_id, src_path, dest_path, local=False, host=None):
        if local:
            exe_cmd("{docker} cp {src} {name}:{dest}".format(docker=local_docker_cmd(host), name=container_id, src=src_path, dest=dest_path))
        else:
            pass

    def execute_command(self, container_id, cmd, local=False, host=None):
        if local:
            exe_cmd("{docker} exec {name} {cmd}".format(docker=local_docker_cmd(host), name=container_id, cmd=cmd))
        else:
            self.operator.execute_container_cmd(container_id, cmd)

    def load_create_params(self, **kwargs):
        '''
            name: 名称
            image: 创建机器的镜像
            flavor: 云主机类型
            system_type: 系统类型
            networks: [{
                'net_id': 'xxxx',
                'fixed_ip': 'xxxx',
            }, {
                'net_id': 'xxxx',
                'fixed_ip': 'xxxx',
            }, {
                'port_id': 'xxxx',
            }]
            float_ip: 浮动ip
            custom_script: 程序自定义脚本
            init_script: 初始化脚本
            install_script: 安装脚本
            users: [{
                'username': 'xxxxxx',
                'password': '******',
            }]
            report_started: 启动上报参数
            report_inited: 初始化上报参数
        '''
        nics = []
        for network in kwargs.get('networks', []):
            if 'net_id' in network:
                nics.append({
                    'network': network['net_id'],
                    'v4-fixed-ip': network['fixed_ip'],
                })
            elif 'port_id' in network:
                nics.append({
                    'port': network['port_id'],
                })

        params = {
            'name': str_filter(kwargs['name']),
            'image': kwargs['image'],
            'flavor': kwargs['flavor'],
            'system_type': kwargs['system_type'],
            'users': kwargs.get('users'),
            'nics': nics,
            'floating_ip': kwargs.get('float_ip'),
            'attach_url': kwargs.get('attach_url'),
            'custom_script': kwargs.get('custom_script'),
            'init_script': kwargs.get('init_script'),
            'install_script': kwargs.get('install_script'),
            'report_started': kwargs.get('report_started'),
            'report_inited': kwargs.get('report_inited'),
        }

        return params

    def local_create(self, **kwargs):
        container_name = str(uuid.uuid4())
        image = kwargs['image']
        ports = kwargs.get('ports', [])
        port_info = kwargs.get('port_info') or {port: get_new_valid_port() for port in ports}
        port_str = ''
        for port, proxy_port in port_info.items():
            port_str += ' -p {proxy_port}:{port} '.format(port=port, proxy_port=proxy_port)

        host = kwargs.get('host') or random_docker_host()
        try:
            host_ip = socket.gethostbyname(host)
        except:
            host_ip = host

        cmd = '{docker} run --name {name} -itd {port_str} {image}'.format(
            docker=local_docker_cmd(host),
            name=container_name,
            port_str=port_str,
            image=image,
        )
        logger.info('local create container cmd: %s', cmd)
        try:
            exe_cmd(cmd, raise_exception=True)
        except Exception as e:
            time.sleep(2)
            raise e

        server = type('Container', (object,), {})()
        server.id = container_name
        server.port_info = port_info
        server.id = container_name
        server.host_ip_address = host_ip

        return server


def local_docker_cmd(host=None):
    if host:
        try:
            host = socket.gethostbyaddr(host)[0]
        except:
            host = host
        cmd = 'docker -H tcp://{host} '.format(host=host)
    else:
        cmd = 'docker '

    cmd = cmd + local_docker_params()

    return cmd


def local_docker_compose_cmd(host=None):
    if host:
        try:
            host = socket.gethostbyaddr(host)[0]
        except:
            host = host
        cmd = 'docker-compose -H tcp://{host}:2375 '.format(host=host)
    else:
        cmd = 'docker-compose '

    cmd = cmd + local_docker_params(is_compose=True)

    return cmd


def local_docker_params(is_compose=False):
    ca_path = '/etc/docker/ssl/ca.pem'
    server_cert_path = '/etc/docker/ssl/server-cert.pem'
    server_key_path = '/etc/docker/ssl/server-key.pem'
    if os.path.exists(ca_path) and os.path.exists(server_cert_path) and os.path.exists(server_key_path):
        if is_compose:
            fmt_str = '--tlscacert={} --tlscert={} --tlskey={}'
        else:
            fmt_str = '--tlsverify --tlscacert={} --tlscert={} --tlskey={}'
        return fmt_str.format(ca_path, server_cert_path, server_key_path)
    else:
        return ''


def random_docker_host(tool=None):
    if tool is None:
        tool = copy.copy(api_settings.DOCKER_HOSTS)

    if not tool:
        raise Exception('no valid docker host')

    host = random.choice(tool)
    if host and not ping(host):
        tool.remove(host)
        return random_docker_host(tool)
    else:
        return host
