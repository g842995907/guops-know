# -*- coding: utf-8 -*-
import logging
import socket

from common_proxy.setting import api_settings as proxy_api_settings
from common_scene.complex.views import BaseScene
from common_scene.setting import api_settings as scene_api_settings

from ..base.base import Resource


logger = logging.getLogger(__name__)


class Vm(Resource):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def allowance_check(self, **kwargs):
        return self.operator.scene_allowance_check(**kwargs)

    def clear_allowance(self, check_id):
        self.operator.release_preallocated(check_id)

    def get(self, vm_id):
        return self.operator.get_server(vm_id)

    def is_first_boot(self, vm_id):
        try:
            result = self.operator.check_first_boot(vm_id).get('is_first_boot', False)
        except Exception as e:
            logger.error('get vm[%s] is_first_boot error: %s', vm_id, e)
            result = False
        return result

    def create(self, **kwargs):
        params = self.load_create_params(**kwargs)
        server = self.send_create(**params)
        server = self.check_create(server, **params)
        return server

    def send_create(self, **params):
        server = self.operator.scene_send_create_server(**params)
        return server

    def check_create(self, server, **params):
        server = self.operator.scene_check_create_server(server, **params)
        return server

    def create_qos(self, name, vm_id=None, network_id=None, rule=None):
        instance = self.get(vm_id) if vm_id else None
        return self.operator.scene_create_qos(name=name, instance=instance, network_id=network_id, rule=rule)

    def update(self, vm_id, **kwargs):
        groups = kwargs.get('groups')
        if groups:
            self.operator.update_instance_security_group(vm_id, groups)
        float_ip = kwargs.get('float_ip')
        if float_ip:
            self.operator.bind_fip(float_ip, port=kwargs.get('fip_port'), instance=self.get(vm_id))

    def delete(self, vm_id, sync=True):
        self.operator.delete_instance(vm_id, sync)

    def pause(self, vm_id):
        self.operator.pause_instance(vm_id)

    def unpause(self, vm_id):
        self.operator.unpause_instance(vm_id)

    def start(self, vm_id):
        return self.operator.start_instance(vm_id)

    def shutdown(self, vm_id):
        return self.operator.shutdown_instance(vm_id)

    def restart(self, vm_id):
        return self.operator.reboot_instance(vm_id)

    def get_console_url(self, vm_id, proxy=True):
        func_name = 'get_%s_console' % scene_api_settings.CONSOLE_PROTOCOL
        try:
            res = getattr(self.operator, func_name)(vm_id)
        except:
            url = None
        else:
            url = res['url'] if res else None

        if url and proxy and proxy_api_settings.SWITCH:
            ip = socket.gethostbyname('controller')
            url = url.replace('%s:%s' % (ip, scene_api_settings.CONSOLE_PORT),
                              '%s:%s' % (proxy_api_settings.PROXY_IP, scene_api_settings.CONSOLE_PROXY_PORT))
        return url

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
                    'net-id': network['net_id'],
                    'v4-fixed-ip': network['fixed_ip'],
                })
            elif 'port_id' in network:
                nics.append({
                    'port-id': network['port_id'],
                })

        image = kwargs['image']
        block_device_mapping_v2 = None

        # # snapshot
        # from .volume import Volume
        # snapshot = Volume().get(snapshot_name=image)
        # if snapshot:
        #     image = ''
        #     block_device_mapping_v2 = [{
        #         'source_type': 'snapshot',
        #         'delete_on_termination': True,
        #         'boot_index': 0,
        #         'destination_type': 'volume',
        #         'uuid': snapshot.id,
        #     }]

        params = {
            'name': kwargs['name'],
            'image': image,
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
            'block_device_mapping_v2': block_device_mapping_v2,
        }

        return params
