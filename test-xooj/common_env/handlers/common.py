# -*- coding: utf-8 -*-
import json
import logging
import random
import time

from django.conf import settings
from rest_framework.reverse import reverse

from common_framework.utils.cache import CacheProduct

from common_env.models import StandardDevice, Env, EnvTerminal
from common_env.setting import api_settings
from .exceptions import MsgException
from .local_lib import scene


logger = logging.getLogger(__name__)


def random_cidr():
    return '%s.%s.0/24' % (random.choice(api_settings.ENV_SUBNET_SEG), random.randint(16, 100))


def random_cidrs(count, exclude_cidrs=None):
    third_range = range(16, 100)
    cidr_pools = []
    for subnet_seg in api_settings.ENV_SUBNET_SEG:
        for third_number in third_range:
            cidr = '%s.%s.0/24' % (subnet_seg, third_number)
            if not exclude_cidrs or cidr not in exclude_cidrs:
                cidr_pools.append(cidr)
    if count > len(cidr_pools):
        raise Exception('too many cidrs to allocate')
    return random.sample(cidr_pools, count)


def random_ips(cidr, count, exclude_ips=None):
    ip_pools = []
    prefix = cidr[:-4]
    for forth_number in range(100, 200):
        ip_pools.append('%s%s' % (prefix, str(forth_number)))
    if exclude_ips:
        ip_pools = list(set(ip_pools) - set(exclude_ips))
    if count > len(ip_pools):
        raise Exception('no more ip')
    return random.sample(ip_pools, count)


def random_password(len=8):
    return "".join(random.sample('23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ', len))


def parse_system_users(access_modes, random_pwd=True):
    user_dict = {}
    for access_mode in access_modes:
        if access_mode['protocol'] in (EnvTerminal.AccessMode.SSH, EnvTerminal.AccessMode.RDP, EnvTerminal.AccessMode.CONSOLE):
            username = access_mode.get('username')
            if username and username not in user_dict:
                password = access_mode.get('password') or (random_password() if random_pwd else '')
                access_mode['password'] = password
                user_dict[username] = {
                    'username': username,
                    'password': password,
                }
    return user_dict.values()


def log_env(env_pk, message, params=None):
    log = Env.objects.filter(pk=env_pk).values('log')[0]['log']
    try:
        log = json.loads(log)
    except:
        log = []
    log.append({'message': message, 'params': params})
    Env.objects.filter(pk=env_pk).update(log=json.dumps(log))


class StandardDeviceTmpVmCreater(object):
    def __init__(self, image, device):
        self.image = image
        self.device = device
        self.ret = {
            'network_ids': [],
            'net_ports': [],
            'router_ids': [],
            'vm_id': None,
            'docker_id': None,
            'float_ip': None,
            'username': None,
            'password': None,
            'host_ip': None,
            'host_name': None,
        }

    def create_resource(self):
        logger.info('device[%s] tmp vm create start', self.device.name)
        try:
            network_info = {}
            if self.device.lan_number:
                try:
                    lan_configs = json.loads(self.device.lan_configs)
                    cidrs = [lan_config.get('cidr') for lan_config in lan_configs if lan_config.get('cidr')]
                except:
                    cidrs = []

                rand_cidrs_count = self.device.lan_number - len(cidrs)
                if rand_cidrs_count:
                    rand_cidrs = random_cidrs(rand_cidrs_count, exclude_cidrs=cidrs)
                    cidrs.extend(rand_cidrs)

                for cidr in cidrs:
                    network_id, subnet_id = self._create_tmp_network(cidr)
                    network_info[cidr] = {
                        'id': network_id,
                        'subnet_id': subnet_id,
                    }
            self._create_tmp_instance(network_info)
        except Exception as e:
            logger.error('device[%s] tmp vm create error: %s', self.device.name, e)
            self.rollback_resource()
            raise e
        else:
            logger.info('device[%s] tmp vm create end', self.device.name)
            return self.ret

    def rollback_resource(self):
        logger.info('rollback device[%s] tmp vm create start', self.device.name)
        try:
            vm_id = self.ret['vm_id']
            if vm_id:
                scene.vm.delete(vm_id)
            docker_id = self.ret['docker_id']
            if docker_id:
                scene.docker.delete(docker_id)
            net_ports = self.ret['net_ports']
            for port_id in net_ports:
                try:
                    scene.network.delete_port(port_id)
                except:
                    pass
            router_ids = self.ret['router_ids']
            for router_id in router_ids:
                scene.router.delete(router_id)
            network_ids = self.ret['network_ids']
            for network_id in network_ids:
                scene.network.delete(network_id)
        except Exception as e:
            logger.error('rollback device[%s] tmp vm create error: %s', self.device.name, e)
        else:
            logger.info('rollback device[%s] tmp vm create end', self.device.name)

    def resource_name(self, name):
        return '.'.join([api_settings.BASE_GROUP_NAME, 'image-' + self.device.name, name])

    def _create_tmp_network(self, cidr):
        name = self.resource_name('tmp_network')
        network, subnet = scene.network.create(name, cidr=cidr)
        self.ret['network_ids'].append(network['id'])
        return network['id'], subnet['id']

    def _create_external_router(self, subnet_id):
        name = self.resource_name('tmp_router')

        router = scene.router.create(name, subnet_ids=[subnet_id], external_net_id=scene.external_net)
        self.ret['router_ids'].append(router['id'])
        return router['id']

    def _create_tmp_instance(self, network_info):
        name = self.resource_name('tmp_instance')

        networks = []
        if network_info:
            for i, (cidr, net_info) in enumerate(network_info.items()):
                ip = cidr[:-4] + str(random.randint(100, 200))
                networks.append({
                    'net_id': net_info['id'],
                    'fixed_ip': ip,
                })
                if i == 0:
                    self._create_external_router(net_info['subnet_id'])
                    fip_info = scene.network.preallocate_fips(1).items()[0]
                    float_ip = fip_info[0]
                    float_ip_params = {
                        'network_id': net_info['id'],
                        'fixed_ip': ip,
                        'float_ip_id': fip_info[1],
                    }
        else:
            external_port_info = scene.network.preallocate_ports(scene.external_net, 1).items()[0]
            networks.append({'port_id': external_port_info[1]})
            self.ret['net_ports'].append(external_port_info[1])

            float_ip = external_port_info[0]

        self.ret['float_ip'] = float_ip

        params = {
            'name': name,
            'image': self.image,
            'system_type': self.device.system_type,
            'flavor': self.device.flavor,
            'networks': networks,
            'report_started': '"" "%s%s"' % (settings.SERVER_HOST, reverse('common_env:tmp_vm_running', (self.device.pk,))),
        }
        username = self.device.access_user or ('root' if self.device.system_type == StandardDevice.SystemType.LINUX else 'administrator')
        password = self.device.access_password or (random_password() if self.device.init_support else '')
        user = {
            'username': username,
            'password': password
        }
        if self.device.init_support:
            params['users'] = [user]
        self.ret.update(user)

        if self.device.image_type == StandardDevice.ImageType.VM:
            server = scene.vm.create(**params)
            self.ret['vm_id'] = server.id
            self.ret['host_ip'] = getattr(server, 'host_ip', None)
            self.ret['host_name'] = getattr(server, 'host_name', None)
        elif self.device.image_type == StandardDevice.ImageType.DOCKER:
            server = scene.docker.create(**params)
            self.ret['docker_id'] = server.id
            self.ret['host_ip'] = getattr(server, 'host_ip', None)
            self.ret['host_name'] = getattr(server, 'host_name', None)
        else:
            raise MsgException('standard device[%s] invalid image type', self.device.name)

        if network_info:
            network_id = float_ip_params['network_id']
            fixed_ip = float_ip_params['fixed_ip']
            float_ip_id = float_ip_params['float_ip_id']
            if self.device.image_type == StandardDevice.ImageType.VM:
                fip_port = scene.network.get_port(network_id, instance=server)
                port_info = '_'.join([fip_port['id'], fixed_ip])
                scene.vm.update(server.id, fip_port=port_info, float_ip=float_ip_id)
            elif self.device.image_type == StandardDevice.ImageType.DOCKER:
                fip_port = scene.network.get_port(network_id, container=server)
                port_info = '_'.join([fip_port['id'], fixed_ip])
                scene.docker.update(server.id, fip_port=port_info, float_ip=float_ip_id)

        return server.id


class DockerLockException(Exception):
    pass


class docker_create_lock(object):

    def __init__(self, envterminal, timeout=api_settings.MAX_DOCKER_BLOCK_SECONDS, key_prefix=None, extra_cidrs=None):
        from .config import INTERNET_NET_ID_PREFIX
        cidrs = []
        for net in envterminal.nets.all():
            if net.cidr:
                cidrs.append(net.cidr)
            elif net.sub_id.lower().startswith(INTERNET_NET_ID_PREFIX):
                cidrs.append(INTERNET_NET_ID_PREFIX)

        if extra_cidrs:
            cidrs.extend(extra_cidrs)
        self.cidrs = cidrs
        self.key_prefix = key_prefix or ''
        self.timeout = timeout

        self._locked_cidrs = []

    def __enter__(self):
        self.get_locks()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_locks()

    @property
    def cache(self):
        if not hasattr(self, '_cache'):
            cls = self.__class__
            self._cache = CacheProduct('{}.{}'.format(cls.__module__, cls.__name__))
        return self._cache

    def gkey(self, cidr):
        return 'docker_lock:{key_prefix}:{cidr}'.format(
            key_prefix=self.key_prefix,
            cidr=cidr,
        )

    def get_lock(self, cidr):
        key = self.gkey(cidr)
        result = self.cache.add(key, 1, self.timeout)
        if result:
            self._locked_cidrs.append(cidr)

        return result

    def release_lock(self, cidr):
        key = self.gkey(cidr)
        self.cache.delete(key)
        self._locked_cidrs.remove(cidr)

    def get_locks(self):
        for cidr in self.cidrs:
            if not self.get_lock(cidr):
                raise DockerLockException()

    def release_locks(self):
        for cidr in self._locked_cidrs:
            self.release_lock(cidr)


class attempt_create_docker_lock(object):

    def __init__(self, envterminal, block=2):
        self.d_lock = docker_create_lock(envterminal)
        self.block = block
        self.time = (api_settings.MAX_DOCKER_BLOCK_SECONDS / block) or 1

    def __enter__(self):
        for i in xrange(self.time):
            try:
                self.d_lock.get_locks()
            except DockerLockException as e:
                self.d_lock.release_locks()
                time.sleep(self.block)
            else:
                break

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.d_lock.release_locks()


def get_lastest_image_name(image_name, device=None):
    return image_name
    # # snapshot
    # if not device:
    #     device = StandardDevice.objects.filter(name=image_name).first()
    #
    # if not device:
    #     return image_name
    #
    # if device.image_type != StandardDevice.ImageType.VM:
    #     return image_name
    #
    # snapshot = StandardDeviceSnapshot.objects.filter(
    #     standard_device=device,
    # ).order_by('-create_time').first()
    # if not snapshot:
    #     return image_name
    #
    # return snapshot.name

