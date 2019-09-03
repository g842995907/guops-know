# -*- coding: utf-8 -*-
import copy
import hashlib
import json
import logging
import os
import random
import re
import shutil
import time
import uuid
import socket
import subprocess
import yaml
import zipfile

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import six, timezone
from rest_framework.reverse import reverse

from common_framework.utils.cmd import exe_cmd
from common_framework.utils.delay_task import new_task
from common_framework.utils.enum import Enum
from common_framework.utils.list import valuefilter
from common_framework.utils.models import close_old_connections
from common_framework.utils.network import probe
from common_framework.utils.rest.mixins import CacheModelMixin
from common_framework.utils.unique import generate_unique_key
from common_auth.models import User
from common_remote.managers import RemoteManager
from common_proxy.nginx import get_new_valid_port
from common_scene.utils import memcache_lock, MemcacheLockException
from common_flowmonitor.views import FlowMonitor

from system_configuration.models import SystemConfiguration

from common_env.models import *
from common_env.setting import api_settings
from common_env.utils.permission import is_admin
from common_env.utils.vis_config import backend_to_vis
from . import pool
from .common import random_cidrs, random_ips, parse_system_users, log_env, attempt_create_docker_lock, \
    get_lastest_image_name
from .local_lib import proxy as local_proxy, scene
from .local_lib.scene.scene.docker import local_docker_compose_cmd, random_docker_host
from .error import error
from .exceptions import MsgException, PoolFullException
from .config import is_internet, INTERNET_NET_ID_PREFIX, EnvConfigHandler, IP_OR_CIDR_PATTERN, IP_PATTERN, \
    PORT_OR_RANGE_PATTERN_E, IP_TYPE
from .installer import generate_installers_install_script

logger = logging.getLogger(__name__)


class BaseExecuter(object):
    flag_pattern = re.compile(r'^FLAG\[\d+\]$')
    ip_pattern = re.compile(r'^\w+\.ip$')

    process_envterminal_status = (
        EnvTerminal.Status.CREATING,
        EnvTerminal.Status.CREATED,
        EnvTerminal.Status.HATCHING,
        EnvTerminal.Status.HATCHED,
        EnvTerminal.Status.STARTING,
        EnvTerminal.Status.STARTED,
        EnvTerminal.Status.DEPLOYING,
        EnvTerminal.Status.RUNNING,
        EnvTerminal.Status.PAUSE,
    )

    message = Enum(
        CREATE_ENV_START='x_create_env_start',
        CREATE_ENV_ERROR='x_create_env_error',
        CREATE_ENV_END='x_create_env_end',

        CREATE_NETWORK_START='x_create_network_start',
        CREATE_NETWORK_ERROR='x_create_network_error',
        CREATE_NETWORK_END='x_create_network_end',
        CREATE_ROUTER_START='x_create_router_start',
        CREATE_ROUTER_ERROR='x_create_router_error',
        CREATE_ROUTER_END='x_create_router_end',
        CREATE_FIREWALL_START='x_create_firewall_start',
        CREATE_FIREWALL_ERROR='x_create_firewall_error',
        CREATE_FIREWALL_END='x_create_firewall_end',
        CREATE_QOS_START='x_create_qos_start',
        CREATE_QOS_ERROR='x_create_qos_error',
        CREATE_QOS_END='x_create_qos_end',
        CREATE_TERMINAL_START='x_create_terminal_start',
        CREATE_TERMINAL_ERROR='x_create_terminal_error',
        CREATE_TERMINAL_END='x_create_terminal_end',
        BIND_FLOATING_IP='x_bind_floating_ip',
    )

    def __init__(self, user, backend_admin=False, proxy=True, remote=True):
        self.user = user
        self.backend_admin = backend_admin
        self.proxy = proxy and local_proxy.PROXY_SWITCH
        self.remote = remote

    # 环境数量上限
    @classmethod
    def get_all_env_limit(cls):
        system_configuration = SystemConfiguration.objects.filter(key='all_env_count').first()
        all_env_limit = system_configuration.value.strip() if system_configuration else None
        try:
            all_env_limit = int(all_env_limit)
        except:
            all_env_limit = 0
        return all_env_limit

    # 个人环境数量上限
    @classmethod
    def get_person_env_limit(cls):
        system_configuration = SystemConfiguration.objects.filter(key='person_env_count').first()
        person_env_limit = system_configuration.value.strip() if system_configuration else None
        try:
            person_env_limit = int(person_env_limit)
        except:
            person_env_limit = 0
        return person_env_limit

    # 获取忽略计入限制的环境数量
    @classmethod
    def get_ignored_using_env_count(cls, user):
        count = 0
        for func in api_settings.GET_IGNORED_USING_ENV_COUNT_FUNCS:
            count = count + func(user)
        return count

    def create_proxy(self, ip, ports):
        proxy_ports = local_proxy.create_proxy(ip, ports)
        logger.info('create proxy ip[%s] ports%s: %s' % (ip, ports, proxy_ports))
        return proxy_ports

    def delete_proxy(self, ip, ports):
        try:
            local_proxy.delete_proxy(ip, ports)
        except Exception as e:
            logger.error('delete proxy ip[%s] ports[%s] error: %s' % (ip, ports, e))
        else:
            logger.info('delete proxy ip[%s] ports[%s] ok' % (ip, ports))

    @property
    def remote_manager(self):
        if not hasattr(self, '_remote_manager'):
            self._remote_manager = RemoteManager(self.user)
        return self._remote_manager

    def _add_ssh_connection(self, hostname, port=22, username=None, password=None, private_key=None):
        connection_name = '%s:%s:%s:%s' % (self.user.id, hostname, port, hashlib.md5(str(uuid.uuid4())).hexdigest())
        kwargs = {
            'port': port
        }
        if username:
            kwargs['username'] = username
        if password:
            kwargs['password'] = password
        if private_key:
            kwargs['private_key'] = private_key
        try:
            connection = self.remote_manager.create_ssh_connection(connection_name, hostname, **kwargs)
        except Exception as e:
            logger.error('add ssh connection error: %s' % e)
            return None

        return connection.connection_id

    def _add_rdp_connection(self, hostname, port=3389, username=None, password=None, security=None, system_type=None):
        connection_name = '%s:%s:%s:%s' % (self.user.id, hostname, port, hashlib.md5(str(uuid.uuid4())).hexdigest())
        kwargs = {
            'port': port
        }
        if username:
            kwargs['username'] = username
        if password:
            kwargs['password'] = password
        if security:
            kwargs['security'] = security

        if system_type and system_type == StandardDevice.SystemType.LINUX:
            kwargs['enable-sftp'] = 'true'

        try:
            connection = self.remote_manager.create_rdp_connection(connection_name, hostname, **kwargs)
        except Exception as e:
            logger.error('add rdp connection error: %s' % e)
            return None

        return connection.connection_id

    def _remove_connection(self, connection_id):
        try:
            self.remote_manager.remove_connection(connection_id)
        except Exception as e:
            logger.error('remove connection error: %s' % e)

    def get_ip_type(self, envterminal, hang_info=None):
        # 连接到外网的机器
        if envterminal.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
            return IP_TYPE.OUTER_FIXED

        # 通过外网路由过来的网络可以分浮动ip
        if envterminal.external:
            for envnet in envterminal.nets.all():
                for envgateway in envnet.envgateway_set.all():
                    if envgateway.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
                        return IP_TYPE.FLOAT

        # 场景机器挂载的网络指定可以分浮动ip
        if hang_info and hang_info.get('allocate_float_ip'):
            return IP_TYPE.FLOAT

        # 没有连接任何网络的机器默认连接到外网
        if not hang_info and envterminal.nets.count() == 0:
            return IP_TYPE.OUTER_FIXED

        return IP_TYPE.INNER_FIXED

    def can_reach_externel(self, envterminal):
        # 直连外网
        if envterminal.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
            return True

        # 连接通过外网路由过来的网络
        for envnet in envterminal.nets.all():
            for envgateway in envnet.envgateway_set.all():
                if envgateway.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
                    return True
        return False

    def get_external_envnet(self, envterminal):
        external_envnet = envterminal.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).first()
        if not external_envnet:
            for envnet in envterminal.nets.all():
                for envgateway in envnet.envgateway_set.all():
                    if envgateway.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
                        return envnet
        return external_envnet

    def get_system_users(self, access_modes):
        return parse_system_users(access_modes)

    def _prepare_create_envterminal_resource(self,
                                             envterminal,
                                             ran_ips=None,
                                             float_ip_info=None,
                                             external_port_info=None,
                                             report_started=None,
                                             report_inited=None,
                                             resource_name=None,
                                             attach_url=None,
                                             ignore_init_script=False,
                                             hang_info=None,
                                             resource_pool=None):
        standard_device = StandardDevice.objects.filter(name=envterminal.image).first()
        init_support = standard_device.init_support if standard_device else False

        resource_name = resource_name or envterminal.name
        if standard_device and standard_device.image_type == StandardDevice.ImageType.VM:
            image_name = get_lastest_image_name(standard_device.name, standard_device)
        else:
            image_name = envterminal.image

        params = {
            'name': resource_name,
            'image': image_name,
            'system_type': envterminal.system_type,
            'flavor': envterminal.flavor,
            'attach_url': attach_url,
        }

        networks = []
        net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
        net_config_dict = {net_config['id']: net_config for net_config in net_configs}
        nets = envterminal.nets.all()
        fixed_ip = None
        float_ip = float_ip_info[0] if float_ip_info else None
        external_ip = external_port_info[0] if external_port_info else None
        if float_ip or external_ip:
            if report_started and envterminal.image_type == EnvTerminal.ImageType.VM:
                params['report_started'] = report_started
            if report_inited:
                params['report_inited'] = report_inited

        for net in nets:
            network = None
            is_internet_net = is_internet(net.sub_id)
            # 直连外网
            if is_internet_net:
                if not external_port_info:
                    raise MsgException(error.NO_ENOUGH_FLOATING_IP)
                fixed_ip = external_ip
                network = {'port_id': external_port_info[1]}
                if net.sub_id in net_config_dict:
                    net_config_dict[net.sub_id]['ip'] = fixed_ip
                else:
                    net_configs.append({'id': net.sub_id, 'ip': fixed_ip})
            else:
                has_ip = False
                if net.sub_id in net_config_dict:
                    net_config = net_config_dict[net.sub_id]
                    ip = net_config.get('ip')
                    if ip:
                        network = {'net_id': net.net_id, 'fixed_ip': ip}
                        has_ip = True
                else:
                    net_config = {
                        'id': net.sub_id,
                        'ip': ''
                    }
                    net_configs.append(net_config)
                if not has_ip:
                    ip = ran_ips[net.sub_id].pop(0)
                    network = {'net_id': net.net_id, 'fixed_ip': ip}
                    net_config['ip'] = ip
                fixed_ip = ip

            if network:
                networks.append(network)

        if hang_info:
            if not fixed_ip:
                fixed_ip = hang_info['fixed_ip']
            networks.append({
                'net_id': hang_info['network_id'],
                'fixed_ip': hang_info['fixed_ip']
            })
        # 没有连接任何网络默认连接到外网上
        elif external_ip and len(nets) == 0:
            fixed_ip = external_ip
            networks.append({'port_id': external_port_info[1]})

        params['networks'] = networks

        access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
        if init_support:
            params['users'] = self.get_system_users(access_modes)
            envterminal.access_modes = json.dumps(access_modes)
        if external_port_info:
            envterminal.net_ports = json.dumps([external_port_info[1]])
        envterminal.net_configs = json.dumps(net_configs)
        envterminal.fixed_ip = fixed_ip
        envterminal.float_ip = float_ip or external_ip
        envterminal.save()

        # 执行前需要解析脚本
        def tmp_task(envterminal, params, float_ip_info=None, hang_info=None):
            params['custom_script'] = envterminal.custom_script
            params['install_script'] = envterminal.install_script
            if not ignore_init_script:
                params['init_script'] = envterminal.init_script

            envterminal.create_params = json.dumps(params)
            envterminal.save()
            return self._create_server(envterminal, params)

        task = (tmp_task, (envterminal, params, float_ip_info, hang_info))
        return task

    def _create_server(self, envterminal, params):
        if envterminal.image_type == EnvTerminal.ImageType.VM:
            create_params = scene.vm.load_create_params(**params)
            server = scene.vm.send_create(**create_params)
            status = self._get_update_envterminal_status(envterminal, EnvTerminal.Status.HATCHING)
            if status == EnvTerminal.Status.HATCHING:
                EnvTerminal.objects.filter(pk=envterminal.pk).update(status=status, vm_id=server.id)
            try:
                server = scene.vm.check_create(server, **create_params)
            except Exception as e:
                try:
                    scene.vm.delete(server.id)
                except:
                    pass
                raise e
        elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
            with attempt_create_docker_lock(envterminal):
                create_params = scene.docker.load_create_params(**params)
                server = scene.docker.send_create(**create_params)
                status = self._get_update_envterminal_status(envterminal, EnvTerminal.Status.HATCHING)
                if status == EnvTerminal.Status.HATCHING:
                    EnvTerminal.objects.filter(pk=envterminal.pk).update(status=status, vm_id=server.id)
                try:
                    server = scene.docker.check_create(server, **create_params)
                except Exception as e:
                    try:
                        scene.docker.delete(server.uuid)
                    except:
                        pass
                    raise e
        else:
            raise MsgException('envterminal[%s] invalid image type[%s]' % (envterminal.pk, envterminal.image_type))

        return server

    def execute_create_envterminal_resource(self, task, resource_pool=None, check=False, update_status_func=None,
                                            auto_check=True, failed=None, async=True):
        def sub_execute():
            try:
                self._execute_create_envterminal_resource(task, resource_pool=resource_pool, check=check,
                                                          update_status_func=update_status_func, auto_check=auto_check)
            except Exception as e:
                if failed:
                    failed(e)

        if async:
            new_task(sub_execute, 0, ())
        else:
            sub_execute()

    def _execute_create_envterminal_resource(self, task, resource_pool=None, check=False, update_status_func=None,
                                             auto_check=True):
        # 建机器
        func = task[0]
        args = task[1]
        envterminal = args[0]
        float_ip_info = args[2]
        hang_info = args[3]

        if envterminal.env:
            log_env(envterminal.env.pk, self.message.CREATE_TERMINAL_START, {'name': envterminal.name})
        server = func(*args)
        if resource_pool:
            if envterminal.image_type == EnvTerminal.ImageType.VM:
                resource_pool['vms'].append(server.id)
            elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                resource_pool['dockers'].append(server.id)

        # 绑定浮动ip
        if float_ip_info:
            external_envnet = self.get_external_envnet(envterminal)
            fixed_ip = None
            network_id = None
            # 默认分配浮动ip
            if external_envnet:
                if not is_internet(external_envnet.sub_id):
                    net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                    net_sub_id_ip = {net_config['id']: net_config['ip'] for net_config in net_configs}
                    fixed_ip = net_sub_id_ip[external_envnet.sub_id]
                    network_id = external_envnet.net_id
            # 统一的外网分配浮动ip
            elif hang_info and hang_info.get('allocate_float_ip'):
                fixed_ip = hang_info['fixed_ip']
                network_id = hang_info['network_id']

            if fixed_ip and network_id:
                log_env(envterminal.env.pk, self.message.BIND_FLOATING_IP, {'name': envterminal.name})
                if envterminal.image_type == EnvTerminal.ImageType.VM:
                    fip_port = scene.network.get_port(network_id, instance=server)
                    port_info = '_'.join([fip_port['id'], fixed_ip])
                    scene.vm.update(server.id, fip_port=port_info, float_ip=float_ip_info[1])
                elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                    fip_port = scene.network.get_port(network_id, container=server)
                    port_info = '_'.join([fip_port['id'], fixed_ip])
                    scene.docker.update(server.id, fip_port=port_info, float_ip=float_ip_info[1])
                EnvTerminal.objects.filter(pk=envterminal.pk).update(float_ip_params=json.dumps({
                    'network_id': network_id,
                    'fixed_ip': fixed_ip,
                    'float_ip_info': float_ip_info,
                }))

        # 此处可能存在机器建好了上报但还未返回的情况，使用update部分更新而不用save
        update_params = {
            'vm_id': server.id,
            'host_name': getattr(server, 'host_name', None),
            'host_ip': getattr(server, 'host_ip_address', None),
        }
        close_old_connections()
        access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
        if self.remote and self._create_remote_connections(envterminal, access_modes):
            update_params['access_modes'] = json.dumps(access_modes)

        float_ip = envterminal.float_ip
        # 没有float_ip的不上报, 不通, 直接置为运行状态(docker 直接延迟两秒置为运行状态)
        is_auto_check = False
        # check主观是否检查状态
        if envterminal.image_type == EnvTerminal.ImageType.VM and check and float_ip:
            # check主观是否自动检查状态
            if auto_check:
                is_auto_check = True
            else:
                # 主观不需自动检查状态时, 而前台也无控制台自己检查时 客观强制实施自动检查
                has_console = EnvTerminal.AccessMode.CONSOLE in [access_mode['protocol'] for access_mode in
                                                                 access_modes]
                if not has_console:
                    is_auto_check = True

        if is_auto_check:
            envterminal_status = EnvTerminal.Status.HATCHED
        else:
            if envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                time.sleep(2)
            envterminal_status = EnvTerminal.Status.RUNNING
            current_time = timezone.now()
            consume_time = current_time - envterminal.create_time
            update_params.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })
            pool.remove_server(envterminal)
        envterminal_status = self._get_update_envterminal_status(envterminal, envterminal_status)

        if update_status_func:
            envterminal.__dict__.update(update_params)
            EnvTerminal.objects.filter(pk=envterminal.pk).update(**update_params)
            update_status_func(envterminal, envterminal_status)
            if envterminal_status not in EnvTerminal.UsingStatusList and check:
                self.check_envterminal_status(envterminal.pk, update_status_func)
        else:
            update_params['status'] = envterminal_status
            envterminal.__dict__.update(update_params)
            EnvTerminal.objects.filter(pk=envterminal.pk).update(**update_params)

    def _create_remote_connections(self, envterminal, access_modes, proxy_port_mapping=None, host_ip=None):
        has_create = False

        if proxy_port_mapping:
            ip = host_ip or settings.SERVER_IP
        else:
            ip = envterminal.float_ip

        if not ip:
            return has_create

        # 建连接
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            if not protocol in [EnvTerminal.AccessMode.SSH, EnvTerminal.AccessMode.RDP]:
                continue

            username = access_mode.get('username')
            if not username:
                continue

            port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort[protocol])
            if proxy_port_mapping:
                port = proxy_port_mapping.get('%s:%s' % (protocol, port))
                if isinstance(port, dict):
                    port = port.get('host_proxy_port')
            if not port:
                continue

            password = access_mode.get('password')

            # need guacamole connection
            if protocol == EnvTerminal.AccessMode.SSH:
                self._update_guacamole_connections(
                    access_mode,
                    self._add_ssh_connection(ip, port, username, password)
                )
                has_create = True
            elif protocol == EnvTerminal.AccessMode.RDP:
                security = access_mode.get('mode')
                rdp_params = {
                    'hostname': ip,
                    'port': port,
                    'username': username,
                    'password': password,
                    'system_type': envterminal.system_type,
                }
                if security:
                    rdp_params['security'] = security
                self._update_guacamole_connections(
                    access_mode,
                    self._add_rdp_connection(**rdp_params)
                )
                has_create = True

        return has_create

    def check_envterminal_status(self, envterminal_pk, update_func):
        new_task(self._check_envterminal_status, 0, (envterminal_pk, update_func))

    # 探测检查机器更新状态
    def _check_envterminal_status(self, envterminal_pk, update_func):
        try:
            envterminal = EnvTerminal.objects.get(pk=envterminal_pk)
        except EnvTerminal.DoesNotExist as e:
            logger.error('check envterminal status error: %s', e)
            return

        standard_device = StandardDevice.objects.filter(name=envterminal.image).first()
        # 有对应标靶明确知道支持初始化的会上报不需要探测检查, 否则执行探测检查
        need_probe = (not standard_device.init_support) if standard_device else True

        limit_time = 60 * 5
        step_time = 1
        if need_probe:
            port = None
            # 有对应标靶并且有访问端口的情况检查端口
            if standard_device and standard_device.access_port:
                port = int(standard_device.access_port)
            # 尝试从标靶访问方式获取默认端口
            elif standard_device and standard_device.access_mode:
                port = EnvTerminal.AccessModeDefaultPort.get(standard_device.access_mode, None)

            # 找不到标靶端口则从虚拟机配置端口找
            if not port:
                access_modes = json.loads(envterminal.access_modes)
                for access_mode in access_modes:
                    protocol = access_mode['protocol']
                    port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort.get(protocol, None))
                    if port:
                        break

            def _callback():
                try:
                    update_func(envterminal, EnvTerminal.Status.RUNNING)
                except Exception as e:
                    logger.error(
                        'probe check - update envterminal status[envterminal_id=%s] error: %s' % (envterminal.id, e))

            probe(
                envterminal.float_ip,
                port,
                limit_time=limit_time,
                step_time=step_time,
                log_prefix='envterminal status[envterminal_id=%s]' % envterminal.id,
                callback=_callback,
                timeout_callback=_callback
            )
        else:
            # 上报模式只设置超时检查
            all_time = 0
            while True:
                logger.info('normal check - envterminal status[envterminal_id=%s]: %ss' % (envterminal.id, all_time))
                try:
                    latest_envterminal = EnvTerminal.objects.get(pk=envterminal.pk)
                except EnvTerminal.DoesNotExist as e:
                    logger.error('normal check - envterminal [%s] not exist' % envterminal.pk)
                    continue
                except Exception as e:
                    logger.error('normal check - get envterminal[%s] error: %s' % (envterminal.pk, e))
                    continue

                if latest_envterminal.status == EnvTerminal.Status.DELETED or \
                        latest_envterminal.status == EnvTerminal.Status.ERROR or \
                        latest_envterminal.status == EnvTerminal.Status.RUNNING or \
                        latest_envterminal.status == EnvTerminal.Status.PAUSE:
                    break
                else:
                    if all_time > limit_time:
                        try:
                            update_func(envterminal, EnvTerminal.Status.RUNNING)
                        except Exception as e:
                            logger.error(
                                'normal check - update envterminal status[envterminal_id=%s] error: %s' % (
                                envterminal.id, e))
                        break
                    else:
                        time.sleep(step_time)
                        all_time += step_time

    # 获取正在更新的服务器最新状态（虚拟机的上报可能快于返回）
    def _get_update_envterminal_status(self, envterminal, status):
        try:
            latest_envterminal = EnvTerminal.objects.get(pk=envterminal.pk)
        except EnvTerminal.DoesNotExist, e:
            return envterminal.status
        if latest_envterminal.status in self.process_envterminal_status and status in self.process_envterminal_status:
            if latest_envterminal.status > status:
                return latest_envterminal.status
        return status

    def _update_guacamole_connections(self, access_mode, connection_id):
        connections = access_mode.get('connections', {})
        connection = connections.get(self.user.id, {})
        connection['connection_id'] = connection_id
        connections[self.user.id] = connection
        access_mode['connections'] = connections

    def _delete_envterminal_resource(self, envterminal, local=False):
        proxy_restart_flag = False
        if envterminal.vm_id:
            if envterminal.image_type == EnvTerminal.ImageType.VM:
                scene.vm.delete(envterminal.vm_id)
            elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                scene.docker.delete(envterminal.vm_id, local=local, host=envterminal.host_ip)

        if envterminal.float_ip_params:
            float_ip_params = json.loads(envterminal.float_ip_params)
            float_ip_info = float_ip_params.get('float_ip_info')
            if float_ip_info:
                try:
                    scene.network.delete_fip(float_ip_info[1])
                except Exception as e:
                    pass

        if envterminal.net_ports:
            net_ports = json.loads(envterminal.net_ports)
            for port_id in net_ports:
                try:
                    scene.network.delete_port(port_id)
                except Exception as e:
                    pass

        if self.remote:
            access_modes = json.loads(envterminal.access_modes)
            for access_mode in access_modes:
                connections = access_mode.get('connections', {})
                for user_id, connection in connections.items():
                    connection_id = connection.get('connection_id')
                    if connection_id:
                        self._remove_connection(connection_id)

        if self.proxy and (envterminal.float_ip or envterminal.host_ip):
            try:
                ports = []
                for key, value in json.loads(envterminal.proxy_port).items():
                    if isinstance(value, dict) and 'host_proxy_port' in value:
                        ports.append(value.get('host_proxy_port'))
                    else:
                        ports.append(key.split(':')[1])
            except Exception as e:
                logger.error('envterminal[%s] delete proxy[%s] error: %s', envterminal.pk, envterminal.proxy_port, e)
            else:
                if ports:
                    proxy_restart_flag = True
                    self.delete_proxy(envterminal.float_ip or envterminal.host_ip, ports)
        return proxy_restart_flag

    def _get_access_mode_key(self, access_mode):
        return '%s:%s:%s' % (access_mode.get('protocol'), access_mode.get('port'), access_mode.get('username'))

    def get_envterminal_console_url(self, envterminal):
        if not envterminal.vm_id or not envterminal.image_type == EnvTerminal.ImageType.VM:
            raise MsgException(error.VM_NOT_EXIST)
        url = scene.vm.get_console_url(envterminal.vm_id)
        return url

    def is_envterminal_first_boot(self, envterminal):
        if not envterminal.vm_id or not envterminal.image_type == EnvTerminal.ImageType.VM:
            return False

        try:
            result = scene.vm.is_first_boot(envterminal.vm_id)
        except:
            result = False
        return result

    def get_single_envterminal_data(self, envterminal):
        access_modes = json.loads(envterminal.access_modes)
        access_mode_map = {self._get_access_mode_key(mode): mode for mode in access_modes}

        if not self.backend_admin:
            raw_access_modes = json.loads(envterminal.raw_access_modes)
            access_mode_map = {self._get_access_mode_key(mode): access_mode_map.get(self._get_access_mode_key(mode), {})
                               for mode in raw_access_modes}

        if self.remote:
            self._supply_user_guacamole_connection(envterminal, access_mode_map)
            for access_mode_key, access_mode in access_mode_map.items():
                connection = access_mode.pop('connections', {}).get(str(self.user.id), {})
                connection_id = connection.get('connection_id')
                if connection_id:
                    remote_manager = RemoteManager(self.user, host=envterminal.host_ip)
                    if access_mode['protocol'] == EnvTerminal.AccessMode.SSH:
                        access_mode['connection_url'] = remote_manager.get_ssh_connection_url(connection_id)
                    elif access_mode['protocol'] == EnvTerminal.AccessMode.RDP:
                        access_mode['connection_url'] = remote_manager.get_rdp_connection_url(connection_id)

        net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
        fixed_ips = [net_config.get('ip') for net_config in net_configs if net_config.get('ip')]

        if self.is_local(envterminal.env):
            proxy_ip = local_proxy.PROXY_IP if self.proxy else envterminal.host_ip
        else:
            proxy_ip = local_proxy.PROXY_IP if self.proxy else None

        data = {
            'status': envterminal.status,
            'fixed_ip': envterminal.fixed_ip,
            'fixed_ips': fixed_ips,
            'float_ip': envterminal.float_ip,
            'proxy_ip': proxy_ip,
            'proxy_port': json.loads(envterminal.proxy_port),
            'host_ip': envterminal.host_ip,
            'access_mode': access_mode_map,
        }

        # if envterminal.image_type == EnvTerminal.ImageType.DOCKER:
        #     data['host_ip'] = envterminal.host_ip
        #     data['host_name'] = envterminal.host_name

        # 获取预估时间
        if envterminal.status in (EnvTerminal.Status.CREATING, EnvTerminal.Status.CREATED,
                                  EnvTerminal.Status.HATCHING, EnvTerminal.Status.HATCHED,
                                  EnvTerminal.Status.STARTING, EnvTerminal.Status.STARTED,
                                  EnvTerminal.Status.DEPLOYING, EnvTerminal.Status.RUNNING, EnvTerminal.Status.PAUSE):
            estimate_consume_seconds = self.get_estimate_envterminal_consume_time(envterminal)
            loaded_seconds, estimate_remain_seconds = self.get_estimate_remain_seconds(envterminal.create_time,
                                                                                       estimate_consume_seconds)
            data['loaded_seconds'] = loaded_seconds
            data['estimate_remain_seconds'] = estimate_remain_seconds
            data['estimate_consume_seconds'] = estimate_consume_seconds
        return data

    def _supply_user_guacamole_connection(self, envterminal, updating_access_mode_map):
        access_modes = json.loads(envterminal.access_modes)
        need_save = False
        for access_mode in access_modes:
            if access_mode['protocol'] not in (
            EnvTerminal.AccessMode.SSH, EnvTerminal.AccessMode.RDP) or not access_mode.get('username'):
                continue

            access_mode_key = self._get_access_mode_key(access_mode)
            if access_mode_key not in updating_access_mode_map:
                continue

            connections = access_mode.get('connections', {})
            connection = connections.get(str(self.user.id), {})
            if not connection and envterminal.float_ip:
                if EnvTerminal.AccessMode.SSH == access_mode['protocol'] and envterminal.float_ip:
                    port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort[EnvTerminal.AccessMode.SSH])
                    connection['connection_id'] = self._add_ssh_connection(
                        envterminal.float_ip,
                        port,
                        access_mode['username'],
                        access_mode.get('password', '')
                    )
                    need_save = True

                if EnvTerminal.AccessMode.RDP == access_mode['protocol'] and envterminal.float_ip:
                    port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort[EnvTerminal.AccessMode.RDP])
                    rdp_params = {
                        'hostname': envterminal.float_ip,
                        'port': port,
                        'username': access_mode['username'],
                        'password': access_mode.get('password', ''),
                        'system_type': envterminal.system_type,
                    }
                    security = access_mode.get('mode')
                    if security:
                        rdp_params['security'] = security
                    connection['connection_id'] = self._add_rdp_connection(**rdp_params)
                    need_save = True
                connections[str(self.user.id)] = connection

            access_mode['connections'] = connections
            updating_access_mode_map[access_mode_key]['connections'] = connections
        if need_save:
            envterminal.access_modes = json.dumps(access_modes)
            envterminal.save()

    # 获取预估的环境创建消耗时间
    @classmethod
    def get_estimate_env_consume_time(cls, json_config):
        estimate_env = Env.objects.filter(
            consume_time__gt=0,
            json_config=json_config,
        ).order_by('-create_time').first()
        consume_time = estimate_env.consume_time if estimate_env else None
        return consume_time

    # 获取预估的机器创建消耗时间
    @classmethod
    def get_estimate_envterminal_consume_time(cls, envterminal):
        estimate_envterminal = EnvTerminal.objects.filter(
            consume_time__gt=0,
            image=envterminal.image,
            install_script=envterminal.install_script,
            init_script=envterminal.init_script
        ).order_by('-create_time').first()
        consume_time = estimate_envterminal.consume_time if estimate_envterminal else None
        return consume_time

    # 转换成预估的剩余秒数
    @classmethod
    def get_estimate_remain_seconds(cls, create_time, consume_time):
        loaded_time = timezone.now() - create_time
        loaded_seconds = int(loaded_time.total_seconds())

        if not consume_time:
            return loaded_seconds, None

        remain_seconds = consume_time - loaded_seconds
        return loaded_seconds, remain_seconds

    def parse_script_val(self, val, sub_id_net=None, flags=None):
        if val == 'PLATFORM_IP':
            return settings.SERVER_IP
        elif val == 'PLATFORM_PORT':
            return settings.SERVER_PORT
        elif self.flag_pattern.match(val):
            if not flags:
                raise MsgException(error.FLAG_INDEX_ERROR.format(val=val))
            index = int(val[5:-1])
            if index > len(flags) - 1:
                raise MsgException(error.FLAG_INDEX_ERROR.format(val=val))
            return flags[index]
        elif self.ip_pattern.match(val):
            if not sub_id_net:
                raise MsgException(error.PARSE_SCRIPT_VARIABLE_ERROR.format(val=val))
            parts = val.spilt('.')
            if len(parts) not in (2, 3):
                raise MsgException(error.PARSE_SCRIPT_VARIABLE_ERROR.format(val=val))
            terminal_sub_id = parts[0]
            if terminal_sub_id not in sub_id_net:
                raise MsgException(error.PARSE_SCRIPT_VARIABLE_ERROR.format(val=val))
            net_info = sub_id_net[terminal_sub_id]
            if len(parts) == 2:
                return net_info.values()[0]
            else:
                net_sub_id = parts[1]
                if net_sub_id not in net_info:
                    raise MsgException(error.PARSE_SCRIPT_VARIABLE_ERROR.format(val=val))
                return net_info[net_sub_id]
        else:
            return val

    def parse_script(self, script, sub_id_net=None, flags=None, return_flags=False):
        if not script:
            if return_flags:
                return script, []
            else:
                return script
        parts = script.split(' ')
        parsed_parts = []
        used_flags = []
        for part in parts:
            if not part:
                continue
            if part.startswith('{') and part.endswith('}'):
                parsed_part = self.parse_script_val(part[1:-1], sub_id_net, flags)
                if parsed_part in flags:
                    used_flags.append(parsed_part)
            else:
                parsed_part = part
            parsed_parts.append(parsed_part)
        if return_flags:
            return ' '.join(parsed_parts), used_flags
        else:
            return ' '.join(parsed_parts)

    def _pause_envterminal(self, envterminal, local=False):
        if envterminal.vm_id:
            if envterminal.image_type == EnvTerminal.ImageType.VM:
                scene.vm.pause(envterminal.vm_id)
            elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                scene.docker.pause(envterminal.vm_id, local=local, host=envterminal.host_ip)

    def _recover_envterminal(self, envterminal, local=False):
        if envterminal.vm_id:
            if envterminal.image_type == EnvTerminal.ImageType.VM:
                scene.vm.unpause(envterminal.vm_id)
            elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                scene.docker.unpause(envterminal.vm_id, local=local, host=envterminal.host_ip)

    @classmethod
    def is_local(cls, env):
        if json.loads(env.hang_info):
            return False

        if env.envnet_set.exclude(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
            return False

        if env.envterminal_set.filter(is_attacker=False).exclude(image_type=EnvTerminal.ImageType.DOCKER).exists():
            return False

        for envterminal in env.envterminal_set.filter(is_attacker=False, image_type=EnvTerminal.ImageType.DOCKER):
            # 拓扑存在自定义的docker不用本地创建
            if StandardDevice.objects.filter(name=envterminal.image, builtin=False).exists():
                return False

        return True


class Creater(BaseExecuter):

    def __init__(self, user, template_env=None,
                 backend_admin=False,
                 proxy=True,
                 remote=True,
                 team=None,
                 flags=None,
                 name_prefix='',
                 ignore_init_script=False,
                 float_ips=None,
                 pre_fips=None,
                 hang_info=None,
                 config=None,
                 executor=None):
        if template_env and template_env.status != Env.Status.TEMPLATE:
            raise MsgException(error.ENV_NOT_CONFIGURED)
        if not template_env and (not config or not config.get('json_config')):
            raise MsgException(error.ENV_NOT_CONFIGURED)

        # template_env从环境模板创建 json_config从配置文件创建
        self.from_config = False if template_env else True
        self.template_env = template_env
        self.config = config
        self.team = team
        self.flags = flags
        self.name_prefix = name_prefix
        self.ignore_init_script = ignore_init_script
        self.float_ips = float_ips
        self.pre_fips = pre_fips
        # 场景连接的外部信息(攻防多个场景的外部网络)
        # {
        #     'terminals': [{
        #         'sub_id': sub_id,
        #         'ignore': false,
        #         'net_id': network_id,
        #         'fixed_ip': fixed_ip,
        #         'allocate_float_ip': false,
        #     }],
        # }
        self.hang_info = hang_info
        self.executor = executor
        super(Creater, self).__init__(user, backend_admin, proxy, remote)

    def resource_name(self, name):
        return '.'.join([api_settings.BASE_GROUP_NAME, self.name_prefix, self.template_env.name, name])

    @classmethod
    def common_resource_name(cls, name, env_name):
        return '.'.join([api_settings.BASE_GROUP_NAME, env_name, name])

    # 创建场景
    def create(self):
        try:
            with memcache_lock(cache, self.create_key, 1, 10):
                env = self.create_env_structure()
        except MemcacheLockException as e:
            raise MsgException(error.DUPLICATE_POST)

        # 加入创建队列
        try:
            for envterminal in env.envterminal_set.all():
                estimate_consume_time = self.get_estimate_envterminal_consume_time(envterminal) or 30
                pool.add_server(envterminal, estimate_consume_time=estimate_consume_time)
        except Exception as e:
            self._error_env(env, e.message)

        # 清除环境缓存
        clear_env_cache()

        log_env(env.pk, self.message.CREATE_ENV_START)
        self._resource = {
            'proxys': {},
            'nets': [],
            'routers': [],
            'firewalls': [],
            'fips': {},
            'external_net_ports': {},
            'vms': [],
            'dockers': [],
            'local_dockers': {},
        }
        self.create_resource(env)

        return env

    # 创建唯一标识
    @property
    def create_key(self):
        if not hasattr(self, '_create_key'):
            self._create_key = hashlib.md5('{}:{}:{}'.format(
                self.user.id,
                self.team.id if self.team else '',
                self.template_env.id if self.template_env else hashlib.md5(self.config['json_config']).hexdigest(),
            )).hexdigest()
        return self._create_key

    def _check_pool(self, server_count, json_config):
        if pool.is_full(need_count=server_count):
            e = PoolFullException(error.CREATE_POOL_FULL)
            if self.executor:
                estimate_env_consume_time = self.get_estimate_env_consume_time(json_config) or 30
                instance = pool.add_executor(self.executor,
                                             consume_count=server_count,
                                             estimate_consume_time=estimate_env_consume_time)
                e.executor_instance = instance
                e.executor_info = pool.get_executor_info(
                    instance=instance
                )
            else:
                e.executor_instance = None
                e.executor_info = {}
            raise e

    # 创建场景结构
    def create_env_structure(self):
        if self.from_config:
            json_config = json.loads(self.config['json_config'])
            server_count = len(json_config.get('servers') or [])
            self._check_pool(server_count, json_config)
        else:
            server_count = self.template_env.envterminal_set.count()
            self._check_pool(server_count, self.template_env.json_config)

        with transaction.atomic():
            if self.from_config:
                config_handler = EnvConfigHandler(self.user, json_config)
                self.template_env = config_handler.create_env_template(
                    type=self.config.get('type', Env.Type.BASE),
                    status=Env.Status.CREATING,
                    team=self.team,
                    file=self.config.get('file'),
                    hang_info=json.dumps(self.hang_info or {}),
                    attackers=self.config.get('attackers') or '[]',
                )
                env = self.template_env
            else:
                env = copy.copy(self.template_env)
                env.pk = None
                env.user = self.user
                env.team = self.team
                env.status = Env.Status.CREATING
                env.hang_info = json.dumps(self.hang_info or {})
                env.create_time = timezone.now()
                env.modify_time = timezone.now()
                env.builtin = False
                env.save()
            self._handle_envnets(env)
            self._handle_envgateways(env)
            self._handle_envterminals(env)

        return env

    def _handle_envnets(self, env):
        if self.from_config:
            return
        self._envnet_subid_id = {}
        for envnet in self.template_env.envnet_set.all():
            envnet.pk = None
            envnet.env = env
            envnet.save()
            self._envnet_subid_id[envnet.sub_id] = envnet.pk

    def _handle_envgateways(self, env):
        if self.from_config:
            return
        for envgateway in self.template_env.envgateway_set.all():
            nets = envgateway.nets.all()
            envgateway.pk = None
            envgateway.env = env
            envgateway.save()
            envgateway.nets.set([self._envnet_subid_id[net.sub_id] for net in nets])

    def _handle_envterminals(self, env):
        template_envterminals = self.template_env.envterminal_set.all()
        if self.backend_admin:
            images = [envterminal.image for envterminal in template_envterminals]
            standart_devices = StandardDevice.objects.filter(name__in=images)
            standart_device_map = {standart_device.name: standart_device for standart_device in standart_devices}

        hang_terminals = self.hang_info.get('terminals', []) if self.hang_info else []
        terminal_hang_dict = {hang_terminal['sub_id']: hang_terminal for hang_terminal in hang_terminals}
        for envterminal in template_envterminals:
            hang_info = terminal_hang_dict.get(envterminal.sub_id)
            if hang_info and hang_info.get('remove'):
                if self.from_config:
                    envterminal.delete()
                else:
                    continue

            nets = envterminal.nets.all()
            if not self.from_config:
                envterminal.pk = None
                envterminal.create_time = timezone.now()
                envterminal.env = env
            envterminal.status = EnvTerminal.Status.CREATING
            if self.backend_admin:
                access_modes = json.loads(envterminal.access_modes)
                protocols = [mode['protocol'] for mode in access_modes]

                # 查询对应标靶的默认系统访问方式
                standart_device = standart_device_map.get(envterminal.image)
                if standart_device and standart_device.access_mode:
                    if standart_device.access_mode not in protocols:
                        access_mode = {
                            'protocol': standart_device.access_mode
                        }
                        if standart_device.access_port:
                            access_mode['port'] = int(standart_device.access_port)
                        if standart_device.access_connection_mode:
                            access_mode['mode'] = standart_device.access_connection_mode
                        if standart_device.access_user:
                            access_mode['username'] = standart_device.access_user
                        if standart_device.access_password:
                            access_mode['password'] = standart_device.access_password
                        access_modes.append(access_mode)
                else:
                    access_mode = {}
                    if envterminal.image_type == EnvTerminal.SystemType.WINDOWS:
                        if EnvTerminal.AccessMode.RDP not in protocols:
                            access_mode['protocol'] = EnvTerminal.AccessMode.RDP
                    elif envterminal.image_type == EnvTerminal.SystemType.LINUX:
                        if EnvTerminal.AccessMode.SSH not in protocols:
                            access_mode['protocol'] = EnvTerminal.AccessMode.SSH
                    if access_mode:
                        if standart_device and standart_device.access_user:
                            access_mode['username'] = standart_device.access_user
                        if standart_device and standart_device.access_password:
                            access_mode['password'] = standart_device.access_password
                        access_modes.append(access_mode)

                envterminal.access_modes = json.dumps(access_modes)
            envterminal.save()
            if not self.from_config:
                envterminal.nets.set([self._envnet_subid_id[net.sub_id] for net in nets])

    def create_resource(self, env):
        is_local = self.is_local(env)
        if is_local:
            new_task(self._local_create_resource, 0, (env,))
        else:
            new_task(self._create_resource, 0, (env,))

    def _local_create_resource(self, env):
        def failed(e):
            logger.error('create env[%s] resource error: %s', env.id, e)
            self._error_env(env, str(e))
            for docker_id, host_ip in self._resource['local_dockers'].items():
                scene.docker.delete(docker_id, local=True, host=host_ip)

        try:
            envterminals = list(env.envterminal_set.all())

            envterminal_sub_id_net = {}
            for envterminal in envterminals:
                net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                envterminal_sub_id_net[envterminal.sub_id] = {net_config['id']: net_config['ip'] for net_config in
                                                              net_configs}

            image_names = [envterminal.image for envterminal in envterminals]
            stantard_devices = StandardDevice.objects.filter(name__in=image_names)
            stantard_device_map = {stantard_device.name: stantard_device for stantard_device in stantard_devices}

            # 解析脚本 (TODO 怎么处理？)
            for envterminal in envterminals:
                # 附加installer工具安装脚本
                stantard_device = stantard_device_map.get(envterminal.image)
                installers = json.loads(envterminal.installers)
                if stantard_device and installers:
                    envterminal.custom_script = generate_installers_install_script(stantard_device.system_sub_type,
                                                                                   installers)
                init_script, used_flags = self.parse_script(envterminal.init_script, envterminal_sub_id_net,
                                                            flags=self.flags, return_flags=True)
                envterminal.init_script = init_script

                envterminal.flags = json.dumps(used_flags)
                envterminal.install_script = self.parse_script(envterminal.install_script, envterminal_sub_id_net,
                                                               flags=self.flags)
                envterminal.deploy_script = self.parse_script(envterminal.deploy_script, envterminal_sub_id_net,
                                                              flags=self.flags)
                envterminal.clean_script = self.parse_script(envterminal.clean_script, envterminal_sub_id_net,
                                                             flags=self.flags)
                envterminal.push_flag_script = self.parse_script(envterminal.push_flag_script, envterminal_sub_id_net,
                                                                 flags=self.flags)
                envterminal.check_script = self.parse_script(envterminal.check_script, envterminal_sub_id_net,
                                                             flags=self.flags)
                envterminal.attack_script = self.parse_script(envterminal.attack_script, envterminal_sub_id_net,
                                                              flags=self.flags)
                envterminal.save()

            image_terminal = {envterminal.image: envterminal for envterminal in envterminals}
            # compose file
            compose_filename = 'docker-compose.yml'
            has_compose_file = False
            if env.file:
                zip_env_file = zipfile.ZipFile(env.file)
                if compose_filename in zip_env_file.namelist():
                    has_compose_file = True

            if has_compose_file:
                host = random_docker_host()
                try:
                    host_ip = socket.gethostbyname(host)
                except:
                    host_ip = host
                has_proxy = False
                y = yaml.load(zip_env_file.read(compose_filename))
                for key, service in y['services'].items():
                    y['services'].pop(key)
                    y['services'][key + generate_unique_key()] = service

                    image = service['image'].split('/')[-1].replace(':', '_')
                    envterminal = image_terminal.get(image)
                    if not envterminal:
                        raise MsgException('no related server with image %s', image)

                    service['image'] = image
                    container_name = generate_unique_key()
                    service['container_name'] = container_name

                    access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
                    port_protocol = {}
                    # 建连接
                    for access_mode in access_modes:
                        protocol = access_mode['protocol']
                        port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort.get(protocol, None))
                        if port:
                            port_protocol[port] = protocol
                    port_info = {port: get_new_valid_port() for port in port_protocol.keys()}
                    service['ports'] = []
                    for port, proxy_port in port_info.items():
                        service['ports'].append('{}:{}'.format(proxy_port, port))

                    host_proxys = []
                    for port, proxy_port in port_info.items():
                        protocol = port_protocol[port]
                        host_proxys.append({
                            'protocol': protocol,
                            'port': port,
                            'proxy_port': proxy_port,
                        })

                    save_proxy_port = {}
                    if host_proxys:
                        has_proxy = True
                        for host_proxy in host_proxys:
                            port = host_proxy['proxy_port']
                            proxy_key = '{}:{}'.format(host_proxy['protocol'], host_proxy['port'])
                            if self.proxy:
                                save_proxy_port[proxy_key] = {
                                    'local_proxy_port': self.create_proxy(host_ip, port),
                                    'host_proxy_port': port,
                                }
                            else:
                                save_proxy_port[proxy_key] = port
                            self._resource['proxys'].setdefault(host_ip, set()).add(port)

                    params = {
                        'vm_id': container_name,
                        'host_ip': host_ip,
                        'proxy_port': json.dumps(save_proxy_port),
                    }
                    envterminal.__dict__.update(params)
                    EnvTerminal.objects.filter(pk=envterminal.pk).update(**params)

                if has_proxy:
                    local_proxy.restart_proxy()

                # add docker default network
                if "networks" not in y.keys():
                    docker_net_name = getattr(api_settings, "DEFAULT_DOCKER_NETWORK", "default_docker_network")
                    y.update({"networks": {"default": {"external": {"name": str(docker_net_name)}}}})

                tmp_file_dir = os.path.join(settings.MEDIA_ROOT, 'tmp', generate_unique_key())
                os.makedirs(tmp_file_dir)
                tmp_file_path = os.path.join(tmp_file_dir, compose_filename)
                try:
                    with open(tmp_file_path, 'w') as f:
                        f.write(yaml.dump(y))
                    exe_cmd('{} -f {} up -d'.format(local_docker_compose_cmd(host), tmp_file_path),
                            raise_exception=True)
                except Exception as e:
                    failed(e)
                else:
                    for envterminal in envterminals:
                        if self.remote:
                            access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
                            proxy_port = json.loads(envterminal.proxy_port) if envterminal.proxy_port else {}
                            if self._create_remote_connections(envterminal, access_modes, proxy_port, host_ip):
                                params = {
                                    'access_modes': json.dumps(access_modes),
                                }
                                envterminal.__dict__.update(params)
                                EnvTerminal.objects.filter(pk=envterminal.pk).update(**params)

                        self.update_envterminal_status(envterminal, EnvTerminal.Status.RUNNING)
                finally:
                    shutil.rmtree(tmp_file_dir)
            else:
                # 创建
                for envterminal in envterminals:
                    def tmp_task(envterminal):
                        try:
                            access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
                            port_protocol = {}
                            # 建连接
                            for access_mode in access_modes:
                                protocol = access_mode['protocol']
                                port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort.get(protocol, None))
                                if port:
                                    port_protocol[port] = protocol

                            # 本地原生docker启动
                            server = scene.docker.local_create(ports=port_protocol.keys(), image=envterminal.image)
                            host_ip = getattr(server, 'host_ip_address', None)
                            self._resource['local_dockers'][server.id] = host_ip

                            port_info = server.port_info
                            host_proxys = []
                            for port, proxy_port in port_info.items():
                                protocol = port_protocol[port]
                                host_proxys.append({
                                    'protocol': protocol,
                                    'port': port,
                                    'proxy_port': proxy_port,
                                })

                            save_proxy_port = {}
                            if host_proxys:
                                for host_proxy in host_proxys:
                                    port = host_proxy['proxy_port']
                                    proxy_key = '{}:{}'.format(host_proxy['protocol'], host_proxy['port'])
                                    if self.proxy:
                                        save_proxy_port[proxy_key] = {
                                            'local_proxy_port': self.create_proxy(host_ip, port),
                                            'host_proxy_port': port,
                                        }
                                    else:
                                        save_proxy_port[proxy_key] = port
                                    self._resource['proxys'].setdefault(host_ip, set()).add(port)
                                local_proxy.restart_proxy()

                            update_params = {
                                'vm_id': server.id,
                                'host_ip': host_ip,
                                'proxy_port': json.dumps(save_proxy_port),
                            }
                            if self.remote and self._create_remote_connections(envterminal, access_modes,
                                                                               save_proxy_port, host_ip):
                                update_params['access_modes'] = json.dumps(access_modes)

                            envterminal.__dict__.update(update_params)
                            EnvTerminal.objects.filter(pk=envterminal.pk).update(**update_params)
                            self.update_envterminal_status(envterminal, EnvTerminal.Status.RUNNING)
                        except Exception as e:
                            failed(e)

                    new_task(tmp_task, 0, (envterminal,))
        except Exception as e:
            failed(e)

    @staticmethod
    def _env_terminal_push_flag(envterminal, env, server_id):
        pushflag_filename = 'pushflag.sh'
        if envterminal.push_flag_script and envterminal.push_flag_script.startswith(pushflag_filename) and env.file:
            zip_env_file = zipfile.ZipFile(env.file)
            tmp_file_dir = os.path.join(settings.MEDIA_ROOT, 'tmp', generate_unique_key())
            os.makedirs(tmp_file_dir)
            tmp_file_path = os.path.join(tmp_file_dir, pushflag_filename)
            try:
                with open(tmp_file_path, 'w') as f:
                    f.write(zip_env_file.read(pushflag_filename))
                scene.docker.cp(server_id, tmp_file_path, '/tmp', local=True, host=envterminal.host_ip)

                # 赋予执行权限
                cmd = "chmod +x '/tmp/{}'".format(envterminal.push_flag_script.split(' ')[0])
                scene.docker.execute_command(server_id, cmd, local=True, host=envterminal.host_ip)

                # 执行pushflag脚本
                cmd = "/bin/sh -c '/tmp/{}'".format(envterminal.push_flag_script)
                scene.docker.execute_command(server_id, cmd, local=True, host=envterminal.host_ip)
            except:
                pass
            finally:
                shutil.rmtree(tmp_file_dir)

    def _create_resource(self, env):
        def failed(e):
            logger.error('create env[%s] resource error: %s', env.id, e)
            self._error_env(env, str(e))
            self._rollback_resource(env)

        try:
            self.check_id = scene.vm.allowance_check(**json.loads(env.json_config))

            envterminals = list(env.envterminal_set.all())

            # 创建网络
            envnets = env.envnet_set.all()
            has_container_envnets = []
            fixed_cidrs = []
            random_cidr_count = 0
            for envnet in envnets:
                # 直接绑定的外网 浮动ip和固定ip视作等同
                if not is_internet(envnet.sub_id):
                    if envnet.cidr:
                        fixed_cidrs.append(envnet.cidr)
                    else:
                        random_cidr_count += 1

                    if envnet.envterminal_set.filter(image_type=EnvTerminal.ImageType.DOCKER).exists():
                        has_container_envnets.append(envnet)
            ran_cidrs = random_cidrs(random_cidr_count, fixed_cidrs)
            for envnet in envnets:
                if not is_internet(envnet.sub_id):
                    if envnet.cidr:
                        self._create_envnet_resource(envnet)
                    else:
                        self._create_envnet_resource(envnet, ran_cidrs.pop(0))

            # 创建网关(路由器、防火墙)
            for envgateway in env.envgateway_set.all():
                self._create_envgateway_resource(envgateway)

            # 创建终端
            # 预分配浮动ip
            hang_terminals = self.hang_info.get('terminals', []) if self.hang_info else []
            terminal_hang_dict = {hang_terminal['sub_id']: hang_terminal for hang_terminal in hang_terminals}
            ip_type_map = {}
            float_ip_count = 0
            outer_ip_count = 0
            for envterminal in envterminals:
                hang_info = terminal_hang_dict.get(envterminal.sub_id)
                # 连到外网的机器能分浮动ip
                ip_type = self.get_ip_type(envterminal, hang_info)
                ip_type_map[envterminal.id] = ip_type
                if ip_type == IP_TYPE.FLOAT:
                    float_ip_count += 1
                elif ip_type == IP_TYPE.OUTER_FIXED:
                    outer_ip_count += 1
            if float_ip_count > 0:
                if self.float_ips is not None:
                    if len(self.float_ips.keys()) < float_ip_count:
                        raise MsgException(error.NO_ENOUGH_FLOATING_IP)
                    float_ips = {}
                    for key in self.float_ips.keys()[:float_ip_count]:
                        float_ips[key] = self.float_ips.pop(key)
                elif self.pre_fips is not None:
                    if len(self.pre_fips) < float_ip_count:
                        raise MsgException(error.NO_ENOUGH_FLOATING_IP)
                    float_ips = scene.network.preallocate_fips(pre_fips=self.pre_fips[:float_ip_count])
                else:
                    float_ips = scene.network.preallocate_fips(float_ip_count)
            else:
                float_ips = {}
            self._resource['fips'] = float_ips
            float_ip_list = float_ips.items()

            # 预分配外网ip
            if outer_ip_count > 0:
                external_net_ports = scene.network.preallocate_ports(scene.external_net, outer_ip_count)
            else:
                external_net_ports = {}
            self._resource['external_net_ports'] = external_net_ports
            external_net_port_list = external_net_ports.items()

            # 预分配固定ip
            declared_ips = {}
            random_ip_count = {}
            net_sub_id_cidr = {}
            for envterminal in envterminals:
                net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                net_config_dict = {net_config['id']: net_config for net_config in net_configs}
                for net in envterminal.nets.all():
                    if not is_internet(net.sub_id):
                        net_sub_id_cidr[net.sub_id] = net.cidr
                        has_ip = False
                        if net.sub_id in net_config_dict:
                            net_config = net_config_dict[net.sub_id]
                            if net_config.get('ip'):
                                declared_ips.setdefault(net.sub_id, []).append(net_config.get('ip'))
                                has_ip = True
                        if not has_ip:
                            ip_count = random_ip_count.get(net.sub_id, 0)
                            ip_count += 1
                            random_ip_count[net.sub_id] = ip_count
            ran_ips = {}
            for net_sub_id, count in random_ip_count.items():
                cidr = net_sub_id_cidr[net_sub_id]
                ran_ips[net_sub_id] = random_ips(cidr, count, declared_ips.get(net_sub_id))

            # 分配ip, 提前创建代理, 分配创建任务
            need_restart_proxy = False
            gateway_tasks = []
            normal_tasks = []
            envterminal_sub_id_net = {}
            for envterminal in envterminals:
                hang_info = terminal_hang_dict.get(envterminal.sub_id)
                prepare_param = {
                    'envterminal': envterminal,
                    'ran_ips': ran_ips,
                    'report_started': '"env_id={env_id}&vm_id={vm_id}&vm_status={vm_status}" "{report_url}"'.format(
                        env_id=envterminal.env.id,
                        vm_id=envterminal.sub_id,
                        vm_status=EnvTerminal.Status.STARTED,
                        report_url=settings.SERVER_HOST + reverse('common_env:update_vm_status')
                    ),
                    'report_inited': '"env_id={env_id}&vm_id={vm_id}&vm_status={vm_status}" "{report_url}"'.format(
                        env_id=envterminal.env.id,
                        vm_id=envterminal.sub_id,
                        vm_status=EnvTerminal.Status.RUNNING,
                        report_url=settings.SERVER_HOST + reverse('common_env:update_vm_status')
                    ),
                    'resource_name': self.resource_name(envterminal.name),
                    'ignore_init_script': self.ignore_init_script,
                    'hang_info': hang_info,
                    'resource_pool': self._resource,
                }
                if env.file:
                    prepare_param['attach_url'] = settings.SERVER_HOST + env.file.url

                ip_type = ip_type_map[envterminal.id]
                if ip_type == IP_TYPE.FLOAT:
                    prepare_param['float_ip_info'] = float_ip_list.pop(0)
                elif ip_type == IP_TYPE.OUTER_FIXED:
                    prepare_param['external_port_info'] = external_net_port_list.pop(0)
                task = self._prepare_create_envterminal_resource(**prepare_param)

                # 提前创建代理
                if self.proxy and envterminal.float_ip:
                    access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
                    proxy_access_protocols = []
                    proxy_access_ports = []
                    # 建连接
                    for access_mode in access_modes:
                        protocol = access_mode['protocol']
                        port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort.get(protocol, None))
                        if port:
                            proxy_access_protocols.append(protocol)
                            proxy_access_ports.append(port)
                    if proxy_access_ports:
                        need_restart_proxy = True
                        proxy_ports = self.create_proxy(envterminal.float_ip, proxy_access_ports)
                        self._resource['proxys'].setdefault(envterminal.float_ip, set()).update(proxy_access_ports)
                        envterminal_proxy_port = {}
                        for i, proxy_port in enumerate(proxy_ports):
                            protocol = proxy_access_protocols[i]
                            port = proxy_access_ports[i]
                            envterminal_proxy_port['%s:%s' % (protocol, port)] = proxy_port
                        envterminal.proxy_port = json.dumps(envterminal_proxy_port)

                if envterminal.role == EnvTerminal.Role.GATEWAY:
                    gateway_tasks.append(task)
                else:
                    normal_tasks.append(task)
                # 全部net_config已分配好
                net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                envterminal_sub_id_net[envterminal.sub_id] = {net_config['id']: net_config['ip'] for net_config in
                                                              net_configs}

            if need_restart_proxy:
                local_proxy.restart_proxy()

            image_names = [envterminal.image for envterminal in envterminals]
            stantard_devices = StandardDevice.objects.filter(name__in=image_names)
            stantard_device_map = {stantard_device.name: stantard_device for stantard_device in stantard_devices}
            # 根据分配好的ip, 解析脚本
            for envterminal in envterminals:
                # 附加installer工具安装脚本
                stantard_device = stantard_device_map.get(envterminal.image)
                installers = json.loads(envterminal.installers)
                if stantard_device and installers:
                    envterminal.custom_script = generate_installers_install_script(stantard_device.system_sub_type,
                                                                                   installers)
                init_script, used_flags = self.parse_script(envterminal.init_script, envterminal_sub_id_net,
                                                            flags=self.flags, return_flags=True)
                envterminal.init_script = init_script

                envterminal.flags = json.dumps(used_flags)
                envterminal.install_script = self.parse_script(envterminal.install_script, envterminal_sub_id_net,
                                                               flags=self.flags)
                envterminal.deploy_script = self.parse_script(envterminal.deploy_script, envterminal_sub_id_net,
                                                              flags=self.flags)
                envterminal.clean_script = self.parse_script(envterminal.clean_script, envterminal_sub_id_net,
                                                             flags=self.flags)
                envterminal.push_flag_script = self.parse_script(envterminal.push_flag_script, envterminal_sub_id_net,
                                                                 flags=self.flags)
                envterminal.check_script = self.parse_script(envterminal.check_script, envterminal_sub_id_net,
                                                             flags=self.flags)
                envterminal.attack_script = self.parse_script(envterminal.attack_script, envterminal_sub_id_net,
                                                              flags=self.flags)
                envterminal.save()

            # 同步创建虚拟网关机器
            for task in gateway_tasks:
                self.execute_create_envterminal_resource(
                    task,
                    resource_pool=self._resource,
                    check=True,
                    update_status_func=self.update_envterminal_status,
                    auto_check=False,
                    failed=failed,
                    async=False
                )
            # 更新网络网关
            for envnet in envnets:
                if envnet.gateway and envnet.subnet_id:
                    scene.network.update_subnet(envnet.subnet_id, gateway_ip=envnet.gateway)

            for envnet in has_container_envnets:
                pass

            # 异步创建其他机器
            for task in normal_tasks:
                self.execute_create_envterminal_resource(
                    task,
                    resource_pool=self._resource,
                    check=True,
                    update_status_func=self.update_envterminal_status,
                    auto_check=False,
                    failed=failed,
                )

        except Exception as e:
            failed(e)
        finally:
            try:
                scene.vm.clear_allowance(self.check_id)
            except:
                pass

    def _rollback_resource(self, env):
        try:
            if self._resource['proxys']:
                for ip, ports in self._resource['proxys'].items():
                    self.delete_proxy(ip, ports)
                local_proxy.restart_proxy()
            if self._resource['fips']:
                for ip, fip_id in self._resource['fips'].items():
                    try:
                        scene.network.delete_fip(fip_id)
                    except Exception as e:
                        logger.error('create env[%s] resource rollback error: %s', env.id, e)
            for vm_id in self._resource['vms']:
                scene.vm.delete(vm_id)
            for docker_id in self._resource['dockers']:
                scene.docker.delete(docker_id)
            for docker_id, host_ip in self._resource['local_dockers'].items():
                scene.docker.delete(docker_id, local=True, host=host_ip)
            if self._resource['external_net_ports']:
                for ip, port_id in self._resource['external_net_ports'].items():
                    scene.network.delete_port(port_id)
            for firewall_id in self._resource['firewalls']:
                scene.firewall.delete(firewall_id)
            for router_id in self._resource['routers']:
                scene.router.delete(router_id)
            for net_id in self._resource['nets']:
                scene.network.delete(net_id)
        except Exception as e:
            logger.error('create env[%s] resource rollback error: %s', env.id, e)

    def _create_envnet_resource(self, envnet, cidr=None):
        log_env(envnet.env.pk, self.message.CREATE_NETWORK_START, {'name': envnet.name})
        cidr = cidr or envnet.cidr
        dns = json.loads(envnet.dns) if envnet.dns else None
        network, subnet = scene.network.create(self.resource_name(envnet.name), cidr=cidr, dns=dns, dhcp=envnet.dhcp)
        self._resource['nets'].append(network['id'])
        envnet.net_id = network['id']
        envnet.subnet_id = subnet['id']
        envnet.cidr = cidr
        envnet.save()

    def _create_envgateway_resource(self, envgateway):
        nets = envgateway.nets.all()
        if envgateway.type in (EnvGateway.Type.ROUTER, EnvGateway.Type.FIREWALL):
            if envgateway.type == EnvGateway.Type.ROUTER:
                log_env(envgateway.env.pk, self.message.CREATE_ROUTER_START, {'name': envgateway.name})
            subnet_ids = [net.subnet_id for net in nets if net.subnet_id]
            name = self.resource_name(envgateway.name)
            static_routing = json.loads(envgateway.static_routing) if envgateway.static_routing else []
            param = {
                'name': name,
                'static_routing': static_routing,
                'subnet_ids': subnet_ids,
            }
            if envgateway.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
                param['external_net_id'] = scene.external_net
            router = scene.router.create(**param)
            self._resource['routers'].append(router['id'])
            envgateway.router_id = router['id']
            envgateway.save()

    @classmethod
    def common_resource_name(cls, name, env_name):
        return '.'.join([api_settings.BASE_GROUP_NAME, env_name, name])

    @classmethod
    def create_related_resources(cls, env):
        resource = {
            'firewalls': [],
            'policies': [],
        }
        try:
            for envgateway in env.envgateway_set.filter(type=EnvGateway.Type.FIREWALL):
                if not envgateway.firewall_id:
                    log_env(env.pk, cls.message.CREATE_FIREWALL_START, {'name': envgateway.name})
                    network_ids = [net.net_id for net in envgateway.nets.all() if net.net_id]
                    rule = json.loads(envgateway.firewall_rule) if envgateway.firewall_rule else None
                    name = cls.common_resource_name(envgateway.name, env.name)
                    firewall, ingress_rules, egress_rules = scene.firewall.create(name, rule=rule,
                                                                                  network_ids=network_ids)
                    if rule:
                        all_gress_rules = ingress_rules + egress_rules
                        for raw_rule in rule:
                            for gress_rule in all_gress_rules:
                                if scene.firewall.is_same_rule(raw_rule, gress_rule):
                                    raw_rule.setdefault('ids', []).append(gress_rule['id'])
                        envgateway.firewall_rule = json.dumps(rule)
                    resource['firewalls'].append(firewall['id'])
                    envgateway.firewall_id = firewall['id']
                    envgateway.save()

            for envterminal in env.envterminal_set.all():
                if not json.loads(envterminal.policies):
                    policies = []
                    create_func = scene.vm.create_qos if envterminal.image_type == EnvTerminal.ImageType.VM else scene.docker.create_qos
                    net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                    for net_config in net_configs:
                        net_sub_id = net_config['id']
                        rule = {}
                        if net_config.get('egress'):
                            rule['egress'] = net_config.get('egress')
                        if net_config.get('ingress'):
                            rule['ingress'] = net_config.get('ingress')
                        if rule:
                            net = envterminal.nets.filter(sub_id=net_sub_id).first()
                            if net:
                                log_env(env.pk, cls.message.CREATE_QOS_START,
                                        {'terminal_name': envterminal.name, 'net_name': net.name})
                                name = cls.common_resource_name('%s_%s_qos' % (envterminal.name, net_sub_id), env.name)
                                net_id = scene.external_net if is_internet(net_sub_id) else net.net_id
                                policy = create_func(name, envterminal.vm_id, net_id, rule)
                                resource['policies'].append(policy['id'])
                                policies.append(policy['id'])
                    envterminal.policies = json.dumps(policies)
                    envterminal.save()
        except Exception as e:
            logger.info('rollback create firewalls start')
            for firewall_id in resource['firewalls']:
                scene.firewall.delete(firewall_id)
            logger.info('rollback create firewalls end')
            logger.info('rollback create policies start')
            for policy_id in resource['policies']:
                scene.qos.delete(policy_id)
            logger.info('rollback create policies end')
            raise e

    # 更新虚拟机状态
    @classmethod
    def update_envterminal_status(cls, envterminal, status):
        # PS:如果机器已经删除, 也重置为运行状态, 如果环境已删除，再删除环境
        envterminal_update_params = {'status': status}

        # 是否已经最终更新过
        is_running_updated = EnvTerminal.objects.filter(pk=envterminal.pk,
                                                        status__in=EnvTerminal.UsingStatusList).exists()

        # 机器已启动部署完成, 记录启动时间和消耗时间
        if not is_running_updated and status in EnvTerminal.UsingStatusList:
            current_time = timezone.now()
            consume_time = current_time - envterminal.create_time
            envterminal_update_params.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })
            pool.remove_server(envterminal)

            if envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                try:
                    if cls.is_local(envterminal.env):
                        container_id = envterminal.vm_id
                    else:
                        container_id = scene.docker.get(envterminal.vm_id).hostname
                    cls._env_terminal_push_flag(envterminal, envterminal.env, container_id)
                except Exception as e:
                    logger.error('push flag error: %s', e)

        created_flag = False
        EnvTerminal.objects.filter(pk=envterminal.pk).update(**envterminal_update_params)
        # 全部机器都启动部署完了
        if not is_running_updated and status in EnvTerminal.UsingStatusList and not EnvTerminal.objects.filter(
                env=envterminal.env).exclude(
                status__in=EnvTerminal.UsingStatusList).exists():
            # 重新查询环境确保环境信息状态最新
            env = Env.objects.get(pk=envterminal.env.pk)

            # 如果环境已删除，删除环境
            if env.status == Env.Status.CREATING:
                created_flag = True
                try:
                    # 创建qos 防火墙
                    cls.create_related_resources(envterminal.env)

                    # 全部机器都启动部署完了, 记录整个环境启动时间和消耗时间
                    current_time = timezone.now()
                    consume_time = current_time - env.create_time
                    env_update_params = {
                        'created_time': current_time,
                        'consume_time': int(consume_time.total_seconds()),
                        'status': Env.Status.USING,
                    }
                    Env.objects.filter(pk=envterminal.env.pk).update(**env_update_params)
                except Exception as e:
                    cls._error_env(env, str(e))
                    admin_delete_env(env)
                    clear_env_cache()
                    raise e
            elif env.status in Env.UsingStatusList:
                pass
            else:
                # 全部机器都启动部署完了, 记录整个环境启动时间和消耗时间
                current_time = timezone.now()
                consume_time = current_time - env.create_time
                env_update_params = {
                    'created_time': current_time,
                    'consume_time': int(consume_time.total_seconds()),
                }
                Env.objects.filter(pk=envterminal.env.pk).update(**env_update_params)
                admin_delete_env(env)

            # 清除环境缓存
            clear_env_cache()

        if created_flag:
            log_env(envterminal.env.pk, cls.message.CREATE_ENV_END)
            logger.info('create env[env_id=%s] ok', envterminal.env.pk)
            # 调用环境创建完成回调
            callbacks = api_settings.ENV_CREATED_CALLBACKS
            for callback in callbacks:
                callback(env)

    @classmethod
    def _error_env(cls, env, error_message=None):
        logger.error('env[env_id=%s] error: %s' % (env.id, error_message))

        try:
            env.error = error_message
            env.status = Env.Status.ERROR
            env.save()
            # 移出创建队列
            for envterminal in env.envterminal_set.all():
                pool.remove_server(envterminal)
        except Exception as e:
            logger.error('env[env_id=%s] except: %s' % (env.id, e))

        # 调用环境创建完成回调
        callbacks = api_settings.ENV_ERROR_CALLBACKS
        for callback in callbacks:
            callback(env, error_message)


class Updater(BaseExecuter):
    ip_re = re.compile(IP_PATTERN)

    ip_or_cidr_re = re.compile(IP_OR_CIDR_PATTERN)

    port_or_range_e_re = re.compile(PORT_OR_RANGE_PATTERN_E)

    def add_static_routing(self, envgateway, static_route):
        if not envgateway.can_user_configure:
            raise MsgException(error.NO_PERMISSION)

        static_route = self._check_static_routing(static_route)
        static_routing = json.loads(envgateway.static_routing) if envgateway.static_routing else []
        if static_route in static_routing:
            raise MsgException(error.EXIST_STATIC_ROUTE)
        if not envgateway.router_id:
            raise MsgException(error.ROUTER_NOT_PREPARED)

        with transaction.atomic():
            scene.router.add_static_route(envgateway.router_id, static_route)
            static_routing.append(static_route)
            envgateway.static_routing = json.dumps(static_routing)
            envgateway.save()
        return static_routing

    def remove_static_routing(self, envgateway, static_route):
        if not envgateway.can_user_configure:
            raise MsgException(error.NO_PERMISSION)

        static_route = self._check_static_routing(static_route)
        static_routing = json.loads(envgateway.static_routing) if envgateway.static_routing else []
        if static_route not in static_routing:
            raise MsgException(error.INVALID_STATIC_ROUTE)

        with transaction.atomic():
            scene.router.remove_static_route(envgateway.router_id, static_route)
            static_routing.remove(static_route)
            envgateway.static_routing = json.dumps(static_routing)
            envgateway.save()
        return static_routing

    def _check_static_routing(self, static_route):
        route = {
            'destination': static_route.get('destination', ''),
            'gateway': static_route.get('gateway', ''),
        }
        if not self.ip_or_cidr_re.match(route['destination']) or not self.ip_re.match(route['gateway']):
            raise MsgException(error.INVALID_STATIC_ROUTE)
        return route

    def _get_firewall_rule(self, firewall_rule, firewall_rules):
        for rule in firewall_rules:
            if scene.firewall._is_same_rule(firewall_rule, rule):
                return rule
        return None

    def add_firewall_rule(self, envgateway, firewall_rule):
        if not envgateway.can_user_configure:
            raise MsgException(error.NO_PERMISSION)

        firewall_rule = self._check_firewall_rule(firewall_rule)
        current_firewall_rules = json.loads(envgateway.firewall_rule) if envgateway.firewall_rule else []
        if self._get_firewall_rule(firewall_rule, current_firewall_rules):
            raise MsgException(error.EXIST_FIREWALL_RULE)
        if not envgateway.firewall_id:
            raise MsgException(error.FIREWALL_NOT_PREPARED)

        with transaction.atomic():
            ingress_rules, egress_rules = scene.firewall.add_rule(envgateway.firewall_id, firewall_rule)
            for gress_rule in (ingress_rules + egress_rules):
                firewall_rule.setdefault('ids', []).append(gress_rule['id'])

            current_firewall_rules.append(firewall_rule)
            envgateway.firewall_rule = json.dumps(current_firewall_rules)
            envgateway.save()
        return current_firewall_rules

    def remove_firewall_rule(self, envgateway, firewall_rule):
        if not envgateway.can_user_configure:
            raise MsgException(error.NO_PERMISSION)

        firewall_rule = self._check_firewall_rule(firewall_rule)
        current_firewall_rules = json.loads(envgateway.firewall_rule) if envgateway.firewall_rule else []
        current_firewall_rule = self._get_firewall_rule(firewall_rule, current_firewall_rules)
        if not current_firewall_rule:
            raise MsgException(error.INVALID_FIREWALL_RULE)

        with transaction.atomic():
            rule_ids = current_firewall_rule.get('ids', [])
            if rule_ids:
                scene.firewall.remove_rules(envgateway.firewall_id, rule_ids)
            current_firewall_rules.remove(current_firewall_rule)
            envgateway.firewall_rule = json.dumps(current_firewall_rules)
            envgateway.save()
        return current_firewall_rules

    def _check_firewall_rule(self, firewall_rule):
        rule = {
            'protocol': valuefilter(firewall_rule.get('protocol', ''), ('tcp', 'udp', 'icmp', 'any')),
            'action': valuefilter(firewall_rule.get('action', ''), ('allow', 'deny', 'reject')),
            'direction': valuefilter(firewall_rule.get('direction', ''), ('ingress', 'egress', 'both', '')),

            'sourceIP': firewall_rule.get('sourceIP', ''),
            'sourcePort': firewall_rule.get('sourcePort', ''),
            'destIP': firewall_rule.get('destIP', ''),
            'destPort': firewall_rule.get('destPort', ''),
        }
        if not rule['protocol'] \
                or not rule['action'] \
                or not self.ip_or_cidr_re.match(rule['sourceIP']) \
                or not self.ip_or_cidr_re.match(rule['destIP']) \
                or not self.port_or_range_e_re.match(rule['sourcePort']) \
                or not self.port_or_range_e_re.match(rule['destPort']):
            raise MsgException(error.INVALID_FIREWALL_RULE)

        return rule

    def restart_envterminal(self, envterminal):
        if envterminal.image_type == EnvTerminal.ImageType.VM:
            scene.vm.restart(envterminal.vm_id)
        elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
            is_local = self.is_local(envterminal.env)
            scene.docker.restart(envterminal.vm_id, is_local, host=envterminal.host_ip)

    def recreate_envterminal(self, envterminal):
        is_local = self.is_local(envterminal.env)

        # 删机器
        if envterminal.image_type == EnvTerminal.ImageType.VM:
            scene.vm.delete(envterminal.vm_id)
        elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
            scene.docker.delete(envterminal.vm_id, local=is_local, host=envterminal.host_ip)
        # 删qos
        policies = json.loads(envterminal.policies)
        if policies:
            for policy_id in policies:
                scene.qos.delete(policy_id)
            envterminal.policies = '[]'
            envterminal.save()

        EnvTerminal.objects.filter(pk=envterminal.pk).update(status=EnvTerminal.Status.CREATING)
        Env.objects.filter(pk=envterminal.env.pk).update(status=Env.Status.CREATING)

        if is_local:
            new_task(self._local_recreate_envterminal_resource, 0, (envterminal,))
        else:
            new_task(self._recreate_envterminal_resource, 0, (envterminal,))

    def _local_recreate_envterminal_resource(self, envterminal):
        # 建机器
        if envterminal.env:
            log_env(envterminal.env.pk, self.message.CREATE_TERMINAL_START, {'name': envterminal.name})

        estimate_consume_time = self.get_estimate_envterminal_consume_time(envterminal) or 1
        pool.add_server(envterminal, estimate_consume_time=estimate_consume_time)

        try:
            proxy_port = json.loads(envterminal.proxy_port)
            port_info = {}
            for key, p_port in proxy_port:
                if isinstance(p_port, dict):
                    port = p_port.get('host_proxy_port')
                else:
                    port = p_port
                port_info[key.split(':')[-1]] = port
            server = scene.docker.local_create(port_info=port_info, image=envterminal.image)

            EnvTerminal.objects.filter(pk=envterminal.pk).update(
                vm_id=server.id,
            )
            self.update_recreate_envterminal_status(envterminal, EnvTerminal.Status.RUNNING)
        except Exception as e:
            pool.remove_server(envterminal)

    def _recreate_envterminal_resource(self, envterminal):
        # 建机器
        if envterminal.env:
            log_env(envterminal.env.pk, self.message.CREATE_TERMINAL_START, {'name': envterminal.name})

        estimate_consume_time = self.get_estimate_envterminal_consume_time(envterminal) or 30
        pool.add_server(envterminal, estimate_consume_time=estimate_consume_time)

        try:
            params = json.loads(envterminal.create_params)
            server = self._create_server(envterminal, params)

            # 浮动ip
            float_ip_params = json.loads(envterminal.float_ip_params)
            if float_ip_params:
                fixed_ip = float_ip_params['fixed_ip']
                network_id = float_ip_params['network_id']
                float_ip_info = float_ip_params['float_ip_info']
                log_env(envterminal.env.pk, self.message.BIND_FLOATING_IP, {'name': envterminal.name})
                if envterminal.image_type == EnvTerminal.ImageType.VM:
                    fip_port = scene.network.get_port(network_id, instance=server)
                    port_info = '_'.join([fip_port['id'], fixed_ip])
                    scene.vm.update(server.id, fip_port=port_info, float_ip=float_ip_info[1])
                elif envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                    fip_port = scene.network.get_port(network_id, container=server)
                    port_info = '_'.join([fip_port['id'], fixed_ip])
                    scene.docker.update(server.id, fip_port=port_info, float_ip=float_ip_info[1])

            update_params = {
                'vm_id': server.id,
            }
            standard_device = StandardDevice.objects.filter(name=envterminal.image).first()
            init_support = standard_device.init_support if standard_device else False

            # 没有float_ip的不上报, 不通, 直接置为运行状态(docker 直接延迟两秒置为运行状态)

            is_auto_check = (
                        envterminal.image_type == EnvTerminal.ImageType.VM and init_support and envterminal.float_ip)

            if is_auto_check:
                envterminal_status = EnvTerminal.Status.HATCHED
            else:
                if envterminal.image_type == EnvTerminal.ImageType.DOCKER:
                    time.sleep(2)
                envterminal_status = EnvTerminal.Status.RUNNING
                current_time = timezone.now()
                consume_time = current_time - envterminal.create_time
                update_params.update({
                    'created_time': current_time,
                    'consume_time': int(consume_time.total_seconds()),
                })
            envterminal_status = self._get_update_envterminal_status(envterminal, envterminal_status)

            envterminal.__dict__.update(update_params)
            EnvTerminal.objects.filter(pk=envterminal.pk).update(**update_params)
            self.update_recreate_envterminal_status(envterminal, envterminal_status)
            if envterminal_status not in EnvTerminal.UsingStatusList:
                self.check_envterminal_status(envterminal.pk, self.update_recreate_envterminal_status)
        except Exception as e:
            pool.remove_server(envterminal)

    @classmethod
    def recreate_envterminal_related_resources(cls, envterminal):
        resource = {
            'policies': [],
        }
        try:
            if not json.loads(envterminal.policies):
                policies = []
                create_func = scene.vm.create_qos if envterminal.image_type == EnvTerminal.ImageType.VM else scene.docker.create_qos
                net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                for net_config in net_configs:
                    net_sub_id = net_config['id']
                    rule = {}
                    if net_config.get('egress'):
                        rule['egress'] = net_config.get('egress')
                    if net_config.get('ingress'):
                        rule['ingress'] = net_config.get('ingress')
                    if rule:
                        net = envterminal.nets.filter(sub_id=net_sub_id).first()
                        if net:
                            log_env(envterminal.env.pk, cls.message.CREATE_QOS_START,
                                    {'terminal_name': envterminal.name, 'net_name': net.name})
                            name = cls.common_resource_name('%s_%s_qos' % (envterminal.name, net_sub_id),
                                                            envterminal.env.name)
                            net_id = scene.external_net if is_internet(net_sub_id) else net.net_id
                            policy = create_func(name, envterminal.vm_id, net_id, rule)
                            resource['policies'].append(policy['id'])
                            policies.append(policy['id'])
                envterminal.policies = json.dumps(policies)
                envterminal.save()
        except Exception as e:
            logger.info('rollback create policies start')
            for policy_id in resource['policies']:
                scene.qos.delete(policy_id)
            logger.info('rollback create policies end')
            raise e

    # 更新虚拟机状态
    @classmethod
    def update_recreate_envterminal_status(cls, envterminal, status):
        # PS:如果机器已经删除, 也重置为运行状态, 如果环境已删除，再删除环境
        envterminal_update_params = {'status': status}

        # 是否已经最终更新过
        is_running_updated = EnvTerminal.objects.filter(pk=envterminal.pk,
                                                        status__in=EnvTerminal.UsingStatusList).exists()

        # 机器已启动部署完成, 记录启动时间和消耗时间
        if not is_running_updated and status in EnvTerminal.UsingStatusList:
            current_time = timezone.now()
            consume_time = current_time - envterminal.create_time
            envterminal_update_params.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })
            pool.remove_server(envterminal)

        created_flag = False
        EnvTerminal.objects.filter(pk=envterminal.pk).update(**envterminal_update_params)
        if not is_running_updated and status in EnvTerminal.UsingStatusList:
            try:
                # 创建qos
                cls.recreate_envterminal_related_resources(envterminal)
            except Exception as e:
                pass

            if not EnvTerminal.objects.filter(env=envterminal.env).exclude(
                    status__in=EnvTerminal.UsingStatusList).exists():
                # 重新查询环境确保环境信息状态最新
                env = Env.objects.get(pk=envterminal.env.pk)
                # 如果环境已删除，删除环境
                if env.status == Env.Status.CREATING:
                    created_flag = True
                    # 全部机器都启动部署完了
                    Env.objects.filter(pk=envterminal.env.pk).update(status=Env.Status.USING)
                elif env.status in Env.UsingStatusList:
                    pass
                else:
                    # 全部机器都启动部署完了
                    admin_delete_env(env)

                # 清除环境缓存
                clear_env_cache()

        if created_flag:
            log_env(envterminal.env.pk, cls.message.CREATE_ENV_END)
            # 调用环境创建完成回调
            callbacks = api_settings.ENV_CREATED_CALLBACKS
            for callback in callbacks:
                callback(env)

    def pause(self, env, async=True):
        if env.status == Env.Status.USING:
            now_time = timezone.now()
            with transaction.atomic():
                Env.objects.filter(pk=env.pk).update(
                    pause_time=now_time,
                    status=Env.Status.PAUSE
                )
                env.envterminal_set.all().update(
                    pause_time=now_time,
                    status=EnvTerminal.Status.PAUSE,
                )

            is_local = self.is_local(env)
            for envterminal in env.envterminal_set.all():
                if async:
                    new_task(self._pause_envterminal, 0, (envterminal, is_local))
                else:
                    self._pause_envterminal(envterminal, is_local)

    def recover(self, env, async=True):
        if env.status == Env.Status.PAUSE:
            with transaction.atomic():
                Env.objects.filter(pk=env.pk).update(
                    pause_time=None,
                    status=Env.Status.USING
                )
                env.envterminal_set.all().update(
                    pause_time=None,
                    status=EnvTerminal.Status.RUNNING
                )

            is_local = self.is_local(env)
            for envterminal in env.envterminal_set.all():
                if async:
                    new_task(self._recover_envterminal, 0, (envterminal, is_local))
                else:
                    self._recover_envterminal(envterminal, is_local)


class Deleter(BaseExecuter):

    def delete(self, env, async=True):
        self.check_delete(env)
        with transaction.atomic():
            env.envterminal_set.update(status=EnvTerminal.Status.DELETED)
            Env.objects.filter(pk=env.pk).update(status=Env.Status.DELETED)
        # 清除环境缓存
        clear_env_cache()
        self.delete_resource(env, async)

    def check_delete(self, env):
        pass

    def delete_resource(self, env, async=True):
        if async:
            new_task(self._delete_resource, 0, (env,))
        else:
            self._delete_resource(env)

    def _delete_resource(self, env):
        try:
            is_local = self.is_local(env)

            proxy_restart_flag = False
            for envterminal in env.envterminal_set.all():
                pool.remove_server(envterminal)
                return_proxy_restart_flag = self._delete_envterminal_resource(envterminal, is_local)
                if return_proxy_restart_flag:
                    proxy_restart_flag = True

            if proxy_restart_flag:
                # 删完重启代理
                local_proxy.restart_proxy()

            for envgateway in env.envgateway_set.all():
                if envgateway.router_id:
                    scene.router.delete(envgateway.router_id)
                if envgateway.firewall_id:
                    scene.firewall.delete(envgateway.firewall_id)

            for envnet in env.envnet_set.all():
                if envnet.net_id:
                    scene.network.delete(envnet.net_id)

            for envterminal in env.envterminal_set.all():
                policies = json.loads(envterminal.policies)
                for policy_id in policies:
                    scene.qos.delete(policy_id)
        except Exception as e:
            logger.error('delete env[%s] resource error: %s', env.id, e)


class Getter(BaseExecuter):
    def get(self, env, is_complete=False):
        data = self.get_env_data(env)
        if is_complete:
            # 获取攻击事件
            attackers = json.loads(env.attackers) if env.attackers else []
            envattackers = EnvAttacker.objects.filter(id__in=attackers)
            data['envattackers'] = [{'id': envattacker.id, 'name': envattacker.name, 'desc': envattacker.desc} for
                                    envattacker in envattackers]
            envattacker_instances = EnvAttackerInstance.objects.filter(
                attach_env=env,
                status__in=(
                EnvAttackerInstance.Status.CREATING, EnvAttackerInstance.Status.USING, EnvAttackerInstance.Status.PAUSE)
            )
            data['envattacker_instances'] = [{
                'id': instance.id,
                'status': instance.status,
                'envattacker_id': instance.envattacker.id,
                'attach_env_id': instance.attach_env.id if instance.attach_env else None,
                'attach_net_id': instance.attach_net.sub_id if instance.attach_net else None,
                'target_ips': instance.target_ips,
                'attack_intensity': instance.attack_intensity,
            } for instance in envattacker_instances]

            # 创建中的环境返回预估创建时间
            if env.status == Env.Status.CREATING:
                estimate_consume_seconds = self.get_estimate_env_consume_time(env.json_config)
                loaded_seconds, estimate_remain_seconds = self.get_estimate_remain_seconds(env.create_time,
                                                                                           estimate_consume_seconds)
                data['loaded_seconds'] = loaded_seconds
                data['estimate_remain_seconds'] = estimate_remain_seconds
                data['estimate_consume_seconds'] = estimate_consume_seconds

            data['vis_structure'] = self.get_vis_structure(env)
        return data

    def get_env_data(self, env):
        data = {
            'id': env.id,
            'name': env.name,
            'status': env.status,
            'error': env.error,
        }
        return data

    def get_single_envnet_data(self, envnet):
        data = {
            'cidr': envnet.cidr,
        }
        return data

    def get_single_envgateway_data(self, envnet, category):
        data = {
            'static_routing': json.loads(envnet.static_routing) if envnet.static_routing else []
        }
        if category == 'firewall':
            data.update({
                'firewall_rule': json.loads(envnet.firewall_rule) if envnet.firewall_rule else [],
            })
        return data

    def get_vis_structure(self, env):
        sub_id_envnet = {envnet.sub_id: envnet for envnet in env.envnet_set.all()}
        sub_id_envgateway = {envgateway.sub_id: envgateway for envgateway in env.envgateway_set.all()}
        sub_id_envterminal = {envterminal.sub_id: envterminal for envterminal in env.envterminal_set.all()}

        json_config = json.loads(env.json_config)
        vis_structure = backend_to_vis(json_config, backend=False)
        vis_nodes = vis_structure['nodes']
        for node in vis_nodes:
            if node['category'] == 'network':
                node_data = node['data']
                envnet = sub_id_envnet[node_data['id']]
                envnet_data = self.get_single_envnet_data(envnet)
                node_data.update(envnet_data)
            elif node['category'] in ('router', 'firewall'):
                node_data = node['data']
                envgateway = sub_id_envgateway[node_data['id']]
                envgateway_data = self.get_single_envgateway_data(envgateway, node['category'])
                node_data.update(envgateway_data)
            elif node['category'] == 'server':
                node_data = node['data']
                envterminal = sub_id_envterminal[node_data['id']]
                envterminal_data = self.get_single_envterminal_data(envterminal)
                node_data.update(envterminal_data)
        return vis_structure

    # 获取流量数据
    def get_flow_data(self, env, count=1, terminal_sub_ids=None, last_time=None):
        fm = FlowMonitor()
        envterminals = env.envterminal_set.filter(is_attacker=False)
        if terminal_sub_ids:
            envterminals = envterminals.filter(sub_ids__in=terminal_sub_ids)
        flow_data = {}
        for envterminal in envterminals:
            if envterminal.vm_id:
                params = {
                    'instance_id': envterminal.vm_id,
                    'count': count,
                }
                if last_time:
                    params['time_since'] = last_time
                flow_data[envterminal.sub_id] = fm.get_instance_flow_datas(**params)
        return flow_data


class Snapshot(object):

    def __init__(self, user, template_env):
        self.user = user
        self.template_env = template_env

    @classmethod
    def common_resource_name(cls, name, template_env):
        return '.'.join([api_settings.BASE_GROUP_NAME, template_env.name, name + '-snapshot'])

    def create(self):
        logger.info('create env[%s] snapshot start.', self.template_env.id)
        template_env = self.template_env
        need_snapshot_envterminals = EnvTerminal.objects.filter(
            env=template_env
        ).exclude(Q(install_script=None) | Q(install_script=''))
        if need_snapshot_envterminals.count() == 0:
            # 没有需要打快照的机器则返回
            raise MsgException(error.ENV_DOESNOT_NEED_SNAPSHOT)

        env_handler = EnvHandler(self.user, backend_admin=True, proxy=False, remote=False, ignore_init_script=True)
        flags = ['xxxx'] * api_settings.MAX_FLAG_COUNT
        env = env_handler.create(self.template_env, flags, 'snapshot_tmp_env')
        try:
            snapshot_env_map = SnapshotEnvMap.objects.get(template_env=template_env)
            snapshot_env_map.tmp_env = env
            snapshot_env_map.save()
        except SnapshotEnvMap.DoesNotExist as e:
            snapshot_env_map = SnapshotEnvMap.objects.create(
                template_env=template_env,
                tmp_env=env
            )
        # 修改模板状态 创建中
        template_env.image_status = Env.ImageStatus.CREATING
        template_env.save()
        need_snapshot_envterminals.update(
            image_status=EnvTerminal.ImageStatus.CREATING
        )
        # 清除环境缓存
        clear_env_cache()
        return env

    # 临时环境创建完成后，继续创建模板
    @classmethod
    def continue_create(cls, env):
        snapshot_env_map = SnapshotEnvMap.objects.filter(tmp_env=env).first()
        if not snapshot_env_map:
            return None

        template_env = snapshot_env_map.template_env
        logger.info('continue create env[%s] snapshot.', template_env.id)
        # 创建模板
        envterminals = EnvTerminal.objects.filter(env=env).exclude(Q(install_script=None) | Q(install_script=''))
        vm_list = []
        for envterminal in envterminals:
            # 关机后再打快照
            if envterminal.type == EnvTerminal.ImageType.VM:
                scene.vm.shutdown(envterminal.vm_id)
            elif envterminal.type == EnvTerminal.ImageType.DOCKER:
                scene.docker.stop(envterminal.vm_id)
        time.sleep(30)

        template_envterminals = EnvTerminal.objects.filter(env=template_env).exclude(
            Q(install_script=None) | Q(install_script=''))
        sub_id_template_envterminal = {envterminal.sub_id: envterminal for envterminal in envterminals}
        for envterminal in envterminals:
            template_envterminal = sub_id_template_envterminal[envterminal.sub_id]

            def created(image):
                cls.update_envterminal_image_status(template_envterminal, template_env, env, Env.ImageStatus.CREATED)

            def failed(error):
                cls.update_envterminal_image_status(template_envterminal, template_env, env, Env.ImageStatus.CREATED)

            image_name = cls.common_resource_name(envterminal.sub_id)
            if envterminal.type == EnvTerminal.ImageType.VM:
                image = scene.image.create(image_name, vm_id=envterminal.vm_idm, created=created, failed=failed)
            elif envterminal.type == EnvTerminal.ImageType.DOCKER:
                image = scene.image.create(image_name, container_id=envterminal.vm_id, created=created, failed=failed)

            # 删除旧的模板
            if template_envterminal.image_id:
                scene.image.delete(template_envterminal.image_id)
            template_envterminal.image_id = image.id
            template_envterminal.save()

    # 临时环境创建失败回调
    @classmethod
    def error_create(cls, env, error_message):
        snapshot_env_map = SnapshotEnvMap.objects.filter(tmp_env=env).first()
        if not snapshot_env_map:
            return None
        template_env = snapshot_env_map.template_env
        template_env.image_status = Env.ImageStatus.ERROR
        template_env.save()

    # 更新模板状态
    @classmethod
    def update_envterminal_image_status(cls, envterminal, template_env, tmp_env, status):
        envterminal.image_status = status
        with transaction.atomic():
            envterminal.save()
            over_flag = False
            if status == EnvTerminal.ImageStatus.ERROR:
                template_env.image_status = Env.ImageStatus.ERROR
                template_env.save()
                over_flag = True
            elif status == EnvTerminal.ImageStatus.CREATED and not EnvTerminal.objects.filter(env=envterminal.env) \
                    .exclude((Q(install_script=None) | Q(install_script='')) | Q(
                image_status=EnvTerminal.ImageStatus.CREATED)).exists():
                template_env.image_status = Env.ImageStatus.CREATED
                template_env.save()
                over_flag = True
                logger.info('create real create env[%s] snapshot by tmp env[%s] over.', template_env.id, tmp_env.id)

            if over_flag:
                # 删除临时环境
                try:
                    admin_delete_env(tmp_env)
                except Exception as e:
                    logger.error('delete tmp env[%s] error: %s', tmp_env.id, str(e))
                # 清除环境缓存
                clear_env_cache()

    def delete(self):
        # 重置环境的模板状态
        template_env = self.template_env
        template_env.image_status = Env.ImageStatus.NOT_APPLY
        with transaction.atomic():
            template_env.save()
            # 删除镜像
            for envterminal in self.template_env.envterminal_set.all():
                if envterminal.image_id:
                    scene.image.delete(envterminal.image_id)
                    envterminal.image_status = EnvTerminal.ImageStatus.NOT_APPLY
                    envterminal.image_id = None
                    envterminal.save()


api_settings.ENV_CREATED_CALLBACKS.add(Snapshot.continue_create)
api_settings.ENV_ERROR_CALLBACKS.add(Snapshot.error_create)


# 环境处理, 创建销毁环境
class EnvHandler(object):
    def __init__(self, user, **kwargs):
        self.user = user
        self.team = kwargs.get('team', None)
        self.is_admin = is_admin(user)

        self.backend_admin = kwargs.get('backend_admin', False) and self.is_admin
        # 是否代理
        self.proxy = kwargs.get('proxy', True) and local_proxy.PROXY_SWITCH
        self.remote = kwargs.get('remote', True)
        self.getter_class = kwargs.get('getter_class', Getter)
        self.creater_class = kwargs.get('creater_class', Creater)
        self.updater_class = kwargs.get('updater_class', Updater)
        self.deleter_class = kwargs.get('deleter_class', Deleter)
        self.snapshot_class = kwargs.get('snapshot_class', Snapshot)
        self.executor = kwargs.get('executor', None)

    def get(self, env, is_complete=False):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get(env, is_complete)

    def get_flow_data(self, env, count, last_time):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get_flow_data(env, count, last_time=last_time)

    def get_network(self, envnet):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get_single_envnet_data(envnet)

    def get_envterminal(self, envterminal):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get_single_envterminal_data(envterminal)

    def get_envterminal_console_url(self, envterminal):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get_envterminal_console_url(envterminal)

    def is_envterminal_first_boot(self, envterminal):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.is_envterminal_first_boot(envterminal)

    def create(self,
               template_env=None,
               flags=None,
               name_prefix='',
               ignore_init_script=False,
               hang_info=None,
               config=None,
               float_ips=None,
               pre_fips=None):
        creater = self.creater_class(
            self.user,
            template_env=template_env,
            backend_admin=self.backend_admin,
            proxy=self.proxy,
            remote=self.remote,
            team=self.team,
            flags=flags,
            name_prefix=name_prefix,
            ignore_init_script=ignore_init_script,
            float_ips=float_ips,
            pre_fips=pre_fips,
            hang_info=hang_info,
            config=config,
            executor=self.executor,
        )
        return creater.create()

    def delete(self, env, async=True):
        deleter = self.deleter_class(self.user, self.backend_admin, self.proxy, self.remote)
        deleter.delete(env, async)

    def pause(self, env, async=True):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.pause(env, async)

    def recover(self, env, async=True):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.recover(env, async)

    def create_snapshot(self, template_env):
        snapshot = self.snapshot_class(self.user, template_env)
        snapshot.create()

    def delete_snapshot(self, template_env):
        snapshot = self.snapshot_class(self.user, template_env)
        snapshot.delete()

    def add_static_routing(self, envgateway, static_route):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.add_static_routing(envgateway, static_route)

    def remove_static_routing(self, envgateway, static_route):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.remove_static_routing(envgateway, static_route)

    def add_firewall_rule(self, envgateway, firewall_rule):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.add_firewall_rule(envgateway, firewall_rule)

    def remove_firewall_rule(self, envgateway, firewall_rule):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.remove_firewall_rule(envgateway, firewall_rule)

    def recreate_envterminal(self, envterminal):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.recreate_envterminal(envterminal)

    def restart_envterminal(self, envterminal):
        updater = self.updater_class(self.user, self.backend_admin, self.proxy, self.remote)
        updater.restart_envterminal(envterminal)


def clear_env_cache():
    CacheModelMixin.clear_cls_cache([
        'common_env.cms.api.ActiveEnvViewSet',
        'common_env.cms.api.EnvViewSet'
    ])


def admin_delete_env(env, async=True):
    admin_user = User.objects.get(pk=1)
    if isinstance(env, six.integer_types):
        env = Env.objects.get(pk=env)
    env_handler = EnvHandler(admin_user, backend_admin=True)
    env_handler.delete(env, async)


class AttackerCreater(BaseExecuter):
    def __init__(self, user, envattacker, attach_env, attach_envnet, target_ips, attack_intensity, backend_admin=False,
                 proxy=True, remote=True, team=None):
        json_config = envattacker.json_config
        if not json_config:
            raise MsgException(error.NO_CONFIG)
        try:
            config = json.loads(json_config)
            servers = config.get('servers', [])
            if len(servers) == 0:
                raise MsgException(error.NO_CONFIG)
        except Exception as e:
            raise MsgException(error.NO_CONFIG)
        else:
            self.servers = servers
        self.envattacker = envattacker
        self.attach_env = attach_env
        self.attach_envnet = attach_envnet
        self.target_ips = target_ips
        self.attack_intensity = attack_intensity
        self.team = team
        super(AttackerCreater, self).__init__(user, backend_admin, proxy, remote)

    def resource_name(self, name):
        return '.'.join([api_settings.BASE_GROUP_NAME, self.envattacker.name, self.attach_env.name, name])

    @classmethod
    def common_resource_name(cls, name, instance_name):
        return '.'.join([api_settings.BASE_GROUP_NAME, instance_name, name])

    # 创建
    def create(self):
        instance = self.create_instance_structure()
        self._resource = {
            'proxys': {},
            'fips': {},
            'external_net_ports': {},
            'vms': [],
            'dockers': [],
            'local_dockers': {},
            'policies': [],
        }
        self.create_resource(instance)

        return instance

    def create_instance_structure(self):
        instance = EnvAttackerInstance.objects.create(
            envattacker=self.envattacker,
            attach_env=self.attach_env,
            attach_net=self.attach_envnet,
            target_ips=self.target_ips,
            attack_intensity=self.attack_intensity,
            name=self.envattacker.name,
            type=self.envattacker.type,
            desc=self.envattacker.desc,
            file=self.envattacker.file,
            json_config=self.envattacker.json_config,
            user=self.user,
            team=self.team,
        )
        self._create_envterminals(instance)
        return instance

    def _create_envterminals(self, instance):
        envterminals = []
        for server in self.servers:
            attack_intensity = server['attackIntensity']
            if attack_intensity['type'] == EnvTerminal.AttackIntensityType.SCALE:
                scale = attack_intensity['intensity'][self.attack_intensity]
            else:
                scale = 1

            access_modes = server.get('accessMode', [])
            for i in range(scale):
                envterminal = EnvTerminal.objects.create(
                    env=self.attach_env,
                    type=EnvTerminal.Type.OTHER,
                    sub_id=server['id'] + '-instance-' + str(instance.id) + '-' + str(i),
                    name=server['name'],
                    system_type=server['systemType'],
                    image_type=server['imageType'],
                    image=server['image'],
                    role=EnvTerminal.Role.EXECUTER,
                    flavor=server.get('flavor'),
                    init_script=server.get('initScript'),
                    install_script=server.get('installScript'),
                    attack_script=server.get('attackScript'),
                    external=server.get('external', False),
                    raw_access_modes=json.dumps(access_modes),
                    is_attacker=True,
                    attack_intensity=json.dumps(server['attackIntensity']),
                )
                envterminal.nets.set([self.attach_envnet.id])
                instance.servers.add(envterminal.id)
                envterminals.append(envterminal)
        return envterminals

    def create_resource(self, instance):
        new_task(self._create_resource, 0, (instance,))

    def _create_resource(self, instance):
        def failed(e):
            logger.error('create envattacker_instance[%s] resource error: %s', instance.id, e)
            self._error_instance(instance, str(e))
            self._rollback_resource(instance)

        try:
            envterminals = list(instance.servers.all())
            # 预分配浮动ip
            ip_type_map = {}
            float_ip_count = 0
            outer_ip_count = 0
            for envterminal in envterminals:
                # 连到外网的机器能分浮动ip
                ip_type = self.get_ip_type(envterminal)
                ip_type_map[envterminal.id] = ip_type
                if ip_type == IP_TYPE.FLOAT:
                    float_ip_count += 1
                elif ip_type == IP_TYPE.OUTER_FIXED:
                    outer_ip_count += 1

            float_ips = scene.network.preallocate_fips(float_ip_count)
            self._resource['fips'] = float_ips
            float_ip_list = float_ips.items()

            # 预分配外网ip
            if outer_ip_count > 0:
                external_net_ports = scene.network.preallocate_ports(scene.external_net, outer_ip_count)
            else:
                external_net_ports = {}
            self._resource['external_net_ports'] = external_net_ports
            external_net_port_list = external_net_ports.items()

            # 预分配固定ip
            net_sub_id = self.attach_envnet.sub_id
            ran_ips = None
            if not is_internet(net_sub_id):
                allocated_ips = []
                for envterminal in self.attach_envnet.envterminal_set.all():
                    net_configs = json.loads(envterminal.net_configs) if envterminal.net_configs else []
                    net_config_dict = {net_config['id']: net_config for net_config in net_configs}
                    if net_sub_id in net_config_dict:
                        net_config = net_config_dict[net_sub_id]
                        ip = net_config.get('ip')
                        if ip:
                            allocated_ips.append(ip)
                ran_ips = {net_sub_id: random_ips(self.attach_envnet.cidr, instance.servers.count(), allocated_ips)}

            need_restart_proxy = False
            tasks = []
            for envterminal in envterminals:
                prepare_param = {
                    'envterminal': envterminal,
                    'ran_ips': ran_ips,
                    'resource_name': self.resource_name(envterminal.name),
                    'resource_pool': self._resource,
                }
                ip_type = ip_type_map[envterminal.id]
                if ip_type == IP_TYPE.FLOAT:
                    prepare_param['float_ip_info'] = float_ip_list.pop(0)
                elif ip_type == IP_TYPE.OUTER_FIXED:
                    prepare_param['external_port_info'] = external_net_port_list.pop(0)

                if instance.file:
                    prepare_param['attach_url'] = settings.SERVER_HOST + instance.file.url
                task = self._prepare_create_envterminal_resource(**prepare_param)

                # 提前创建代理
                if self.proxy and envterminal.float_ip:
                    access_modes = json.loads(envterminal.access_modes) if envterminal.access_modes else []
                    proxy_access_protocols = []
                    proxy_access_ports = []
                    # 建连接
                    for access_mode in access_modes:
                        protocol = access_mode['protocol']
                        port = access_mode.get('port', EnvTerminal.AccessModeDefaultPort.get(protocol, None))
                        if port:
                            proxy_access_protocols.append(protocol)
                            proxy_access_ports.append(port)
                    if proxy_access_ports:
                        need_restart_proxy = True
                        proxy_ports = self.create_proxy(envterminal.float_ip, proxy_access_ports)
                        self._resource['proxys'].setdefault(envterminal.float_ip, set()).update(proxy_access_ports)
                        envterminal_proxy_port = {}
                        for i, proxy_port in enumerate(proxy_ports):
                            protocol = proxy_access_protocols[i]
                            port = proxy_access_ports[i]
                            envterminal_proxy_port['%s:%s' % (protocol, port)] = proxy_port
                        envterminal.proxy_port = json.dumps(envterminal_proxy_port)

                tasks.append(task)

                # 解析脚本
                envterminal.install_script = self.parse_script(envterminal.install_script)
                if envterminal.init_script:
                    init_script = ' '.join([envterminal.init_script, ' ', self.target_ips])
                    init_script = self.parse_script(init_script)
                    envterminal.init_script = init_script
                envterminal.save()

            if need_restart_proxy:
                local_proxy.restart_proxy()

            for task in tasks:
                self.execute_create_envterminal_resource(
                    task,
                    resource_pool=self._resource,
                    check=False,
                    update_status_func=self.update_envterminal_status,
                    auto_check=False,
                    failed=failed,
                )
        except Exception as e:
            failed(e)

    def _rollback_resource(self, instance):
        try:
            if self._resource['proxys']:
                for ip, ports in self._resource['proxys'].items():
                    self.delete_proxy(ip, ports)
                local_proxy.restart_proxy()
            if self._resource['fips']:
                for ip, fip_id in self._resource['fips'].items():
                    try:
                        scene.network.delete_fip(fip_id)
                    except Exception as e:
                        logger.error('create envattacker_instance[%s] resource rollback error: %s', instance.id, e)
            if self._resource['external_net_ports']:
                for ip, port_id in self._resource['external_net_ports'].items():
                    scene.network.delete_port(port_id)
            for vm_id in self._resource['vms']:
                scene.vm.delete(vm_id)
            for docker_id in self._resource['dockers']:
                scene.docker.delete(docker_id)
            for docker_id, host_ip in self._resource['local_dockers'].items():
                scene.docker.delete(docker_id, local=True, host=host_ip)
        except Exception as e:
            logger.error('create envattacker_instance[%s] resource rollback error: %s', instance.id, e)

    @classmethod
    def create_related_resources(cls, instance):
        resource = {
            'policies': [],
        }
        try:
            # 创建qos
            for envterminal in instance.servers.all():
                attack_intensity = json.loads(envterminal.attack_intensity)
                limit = None
                if attack_intensity['type'] == EnvTerminal.AttackIntensityType.TRAFFIC:
                    limit = attack_intensity['intensity'][instance.attack_intensity]
                elif attack_intensity['type'] == EnvTerminal.AttackIntensityType.SCALE:
                    limit = attack_intensity.get('bandwidth', '')
                    if limit:
                        limit = int(limit)

                if limit:
                    create_func = scene.vm.create_qos if envterminal.image_type == EnvTerminal.ImageType.VM else scene.docker.create_qos
                    rule = {
                        'egress': limit,
                        'ingress': limit,
                    }
                    net = envterminal.nets.first()
                    name = cls.common_resource_name('%s_%s_qos' % (envterminal.name, net.sub_id), instance.name)
                    net_id = scene.external_net if is_internet(net.sub_id) else net.net_id
                    policy = create_func(name, envterminal.vm_id, net_id, rule)
                    resource['policies'].append(policy['id'])
                    envterminal.policies = json.dumps([policy['id']])
                    envterminal.save()
        except Exception as e:
            logger.info('rollback create policies start')
            for policy_id in resource['policies']:
                scene.qos.delete(policy_id)
            logger.info('rollback create policies end')
            raise e

    # 更新虚拟机状态
    @classmethod
    def update_envterminal_status(cls, envterminal, status):
        envterminal_update_params = {'status': status}

        # 是否已经最终更新过
        is_running_updated = EnvTerminal.objects.filter(pk=envterminal.pk,
                                                        status__in=EnvTerminal.UsingStatusList).exists()

        # 机器已启动部署完成, 记录启动时间和消耗时间
        if not is_running_updated and status in EnvTerminal.UsingStatusList:
            current_time = timezone.now()
            consume_time = current_time - envterminal.create_time
            envterminal_update_params.update({
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            })

        EnvTerminal.objects.filter(pk=envterminal.pk).update(**envterminal_update_params)
        instance = EnvAttackerInstance.objects.filter(servers=envterminal).first()
        # 全部机器都启动部署完了
        if not is_running_updated and instance and status in EnvTerminal.UsingStatusList \
                and not instance.servers.exclude(status__in=EnvTerminal.UsingStatusList).exists():
            # 全部机器都启动部署完了, 记录整个环境启动时间和消耗时间
            consume_time = current_time - instance.create_time

            instance_update_params = {
                'created_time': current_time,
                'consume_time': int(consume_time.total_seconds()),
            }
            # 如果环境已删除，删除环境
            if instance.status == EnvAttackerInstance.Status.CREATING:
                try:
                    cls.create_related_resources(instance)
                    instance_update_params['status'] = EnvAttackerInstance.Status.USING
                    EnvAttackerInstance.objects.filter(pk=instance.pk).update(**instance_update_params)
                except Exception as e:
                    cls._error_instance(instance, str(e))
                    admin_delete_attackerinstance(instance)
                    raise e
            elif instance.status in (EnvAttackerInstance.Status.DELETED, EnvAttackerInstance.Status.ERROR):
                EnvAttackerInstance.objects.filter(pk=instance.pk).update(**instance_update_params)
                admin_delete_attackerinstance(instance)

    @classmethod
    def _error_instance(cls, instance, error_message=None):
        try:
            instance.error = error_message
            instance.status = EnvAttackerInstance.Status.ERROR
            instance.save()
            for envterminal in instance.servers.all():
                # 移除连接
                envterminal.env = None
                envterminal.save()
                envterminal.nets.set([])
        except Exception as e:
            logger.error('envattacker_instance[id=%s] error: %s' % (instance.id, e))


class AttackerOperator(BaseExecuter):
    def __init__(self, user, backend_admin=False, proxy=True, remote=True):
        super(AttackerOperator, self).__init__(user, backend_admin, proxy, remote)

    def pause(self, instance, async=True):
        if instance.status == EnvAttackerInstance.Status.USING:
            with transaction.atomic():
                EnvAttackerInstance.objects.filter(pk=instance.pk).update(status=EnvAttackerInstance.Status.PAUSE)
                instance.servers.all().update(status=EnvTerminal.Status.PAUSE)

            for envterminal in instance.servers.all():
                if async:
                    new_task(self._pause_envterminal, 0, (envterminal,))
                else:
                    self._pause_envterminal(envterminal)
        return instance

    def recover(self, instance, async=True):
        if instance.status == EnvAttackerInstance.Status.PAUSE:
            with transaction.atomic():
                EnvAttackerInstance.objects.filter(pk=instance.pk).update(status=EnvAttackerInstance.Status.USING)
                instance.servers.all().update(status=EnvTerminal.Status.RUNNING)

            for envterminal in instance.servers.all():
                if async:
                    new_task(self._recover_envterminal, 0, (envterminal,))
                else:
                    self._recover_envterminal(envterminal)
        return instance


class AttackerDeleter(BaseExecuter):
    def __init__(self, user, backend_admin=False, proxy=True, remote=True):
        super(AttackerDeleter, self).__init__(user, backend_admin, proxy, remote)

    def delete(self, instance, async=True):
        with transaction.atomic():
            instance.servers.update(status=EnvTerminal.Status.DELETED)
            EnvAttackerInstance.objects.filter(pk=instance.pk).update(status=EnvAttackerInstance.Status.DELETED)
        self.delete_resource(instance, async)

    def delete_resource(self, instance, async=True):
        if async:
            new_task(self._delete_resource, 0, (instance,))
        else:
            self._delete_resource(instance)

    def _delete_resource(self, instance):
        try:
            proxy_restart_flag = False
            envterminals = instance.servers.all()
            for envterminal in envterminals:
                return_proxy_restart_flag = self._delete_envterminal_resource(envterminal)
                # 移除连接
                envterminal.env = None
                envterminal.save()
                envterminal.nets.set([])
                if return_proxy_restart_flag:
                    proxy_restart_flag = True

            if proxy_restart_flag:
                # 删完重启代理
                local_proxy.restart_proxy()

            for envterminal in envterminals:
                policies = json.loads(envterminal.policies)
                for policy_id in policies:
                    scene.qos.delete(policy_id)
        except Exception as e:
            logger.error('delete attacker instance[%s] resource error: %s', instance.id, e)


class AttackerGetter(BaseExecuter):
    def get(self, instance, is_complete=False):
        data = self.get_instance_data(instance)
        if is_complete:
            # 创建中的环境返回预估创建时间
            if instance.status == EnvAttackerInstance.Status.CREATING:
                estimate_consume_seconds = self.get_estimate_instance_consume_time(instance)
                loaded_seconds, estimate_remain_seconds = self.get_estimate_remain_seconds(instance.create_time,
                                                                                           estimate_consume_seconds)
                data['loaded_seconds'] = loaded_seconds
                data['estimate_remain_seconds'] = estimate_remain_seconds
                data['estimate_consume_seconds'] = estimate_consume_seconds

            envterminals = []
            for envterminal in instance.server.all():
                envterminal_data = self.get_single_envterminal_data(envterminal)
                if self.backend_admin:
                    envterminal_data.update({
                        'imageType': envterminal.image_type,
                        'systemType': envterminal.system_type,
                        'image': envterminal.image,
                        'initSupport': envterminal.init_support,
                        'external': envterminal.external,
                        'flavor': envterminal.flavor,
                        'accessMode': json.loads(envterminal.accessMode),
                        'initScript': envterminal.initScript,
                        'installScript': envterminal.installScript,
                        'attackScript': envterminal.attackScript,
                    })
                envterminals.append(envterminal_data)
            data['envterminals'] = envterminals
        return data

    def get_instance_data(self, instance):
        data = {
            'id': instance.id,
            'name': instance.name,
            'status': instance.status,
            'error': instance.error,
        }
        return data

    # 获取预估的环境创建消耗时间
    @classmethod
    def get_estimate_instance_consume_time(cls, instance):
        estimate_instance = instance.objects.filter(
            consume_time__gt=0,
            json_config=instance.json_config
        ).order_by('-create_time').first()
        consume_time = estimate_instance.consume_time if estimate_instance else None
        return consume_time


class AttackerHandler(object):

    def __init__(self, user, **kwargs):
        self.user = user
        self.team = kwargs.get('team', None)
        self.is_admin = is_admin(user)

        self.backend_admin = kwargs.get('backend_admin', False) and self.is_admin
        # 是否代理
        self.proxy = kwargs.get('proxy', True)
        self.remote = kwargs.get('remote', True)
        self.getter_class = kwargs.get('getter_class', AttackerGetter)
        self.creater_class = kwargs.get('creater_class', AttackerCreater)
        self.operator_class = kwargs.get('operator_class', AttackerOperator)
        self.deleter_class = kwargs.get('deleter_class', AttackerDeleter)

    def get(self, instance, is_complete=False):
        getter = self.getter_class(self.user, self.backend_admin, self.proxy, self.remote)
        return getter.get(instance, is_complete)

    def create(self, envattacker, attach_env, attach_envnet, target_ips, attack_intensity):
        creater = self.creater_class(self.user, envattacker, attach_env, attach_envnet, target_ips, attack_intensity,
                                     self.backend_admin, self.proxy, self.remote, self.team)
        return creater.create()

    def pause(self, instance, async=True):
        operator = self.operator_class(self.user, self.backend_admin, self.proxy, self.remote)
        return operator.pause(instance, async)

    def recover(self, instance, async=True):
        operator = self.operator_class(self.user, self.backend_admin, self.proxy, self.remote)
        return operator.recover(instance, async)

    def delete(self, instance, async=True):
        deleter = self.deleter_class(self.user, self.backend_admin, self.proxy, self.remote)
        deleter.delete(instance, async)


def admin_delete_attackerinstance(instance, async=True):
    admin_user = User.objects.get(pk=1)
    if isinstance(instance, six.integer_types):
        instance = EnvAttackerInstance.objects.get(pk=instance)
    attacker_handler = AttackerHandler(admin_user, backend_admin=True)
    attacker_handler.delete(instance, async)
