# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import os
import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.utils import six

from rest_framework import exceptions, serializers

from common_framework.utils.rest.request import DataFilter
from common_remote.managers import RemoteManager, MonitorManager
from common_auth.models import User
from common_framework.utils.rest import serializers as common_serializers
from .. import models as env_models
from ..handlers.local_lib import proxy
from ..handlers.config import EnvConfigHandler, AttackerConfigHandler
from ..handlers.manager import Getter
from ..handlers.exceptions import MsgException
from ..setting import api_settings
from ..utils import resource as resource_util

from . import error


logger = logging.getLogger(__name__)


class ActiveEnvSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    servers = serializers.SerializerMethodField()

    def get_creator(self, obj):
        return obj.user.first_name or obj.user.username

    def get_servers(self, obj):
        envterminals = obj.envterminal_set.all()
        data = [{
            'sub_id': envterminal.sub_id,
            'status': envterminal.status,
            'access_modes': envterminal.access_modes,
            'host_ip': envterminal.host_ip,
        } for envterminal in envterminals]
        return data

    class Meta:
        model = env_models.Env
        fields = ('id', 'type', 'name', 'status', 'error', 'servers', 'create_time', 'consume_time', 'creator')
        read_only_fields = ('type', 'name', 'status', 'error', 'servers', 'create_time', 'consume_time', 'creator')

    @classmethod
    def get_monitor_info(cls, data, types=None):
        types = types or ['monitor', 'assistance']
        has_monitor = 'monitor' in types
        has_assistance = 'assistance' in types
        monitor_info = {}
        assistance_info = {}

        host_connections = {}
        conection_server = {}
        user_ids = []
        for row in data:
            if row['status'] == env_models.Env.Status.USING:
                for server in row['servers']:
                    host_ip = server['host_ip'] or ''
                    access_modes = json.loads(server['access_modes'])
                    for access_mode in access_modes:
                        connections = access_mode.get('connections', {})
                        for user_id, connection in connections.items():
                            connection_id = connection['connection_id']
                            host_connections.setdefault(host_ip, []).append(connection_id)
                            conection_server[connection_id] = {
                                'env_id': row['id'],
                                'user_id': int(user_id),
                                'server_sub_id': server['sub_id'],
                            }
                            user_ids.append(user_id)

        users = User.objects.filter(pk__in=user_ids)
        user_map = {user.id: {
            'user_id': user.id,
            'username': user.first_name,
            'first_name': user.first_name
        } for user in users}

        for host_ip, connections in host_connections.items():
            monitor_manager = MonitorManager(host=host_ip)
            if has_monitor:
                try:
                    monitor_ret = monitor_manager.share_active_sessions_for_monitor(connection_ids=connections)
                except:
                    pass
                else:
                    for connection_id, ret in monitor_ret.items():
                        server_info = conection_server[connection_id]
                        monitor_info.setdefault(server_info['env_id'], []).append({
                            'sub_id': server_info['server_sub_id'],
                            'user': user_map[server_info['user_id']],
                            'link': ret['cyberpeace_monitor'],
                        })

            if has_assistance:
                try:
                    assistance_ret = monitor_manager.share_active_sessions_for_assistance(connection_ids=connections)
                except:
                    pass
                else:
                    for connection_id, ret in assistance_ret.items():
                        server_info = conection_server[connection_id]
                        assistance_info.setdefault(server_info['env_id'], []).append({
                            'sub_id': server_info['server_sub_id'],
                            'user': user_map[server_info['user_id']],
                            'link': ret['cyberpeace_assistance'],
                        })

        ret = {}
        if has_monitor:
            ret['monitor_info'] = monitor_info
        if has_assistance:
            ret['assistance_info'] = assistance_info

        return ret


class EnvSerializer(serializers.ModelSerializer,
                    common_serializers.BaseShareSerializer,
                    common_serializers.CreateUserNameAndShareSerializer):
    tag = serializers.SerializerMethodField()
    has_file = serializers.SerializerMethodField()
    env_file = serializers.SerializerMethodField()
    vis_config = serializers.SerializerMethodField()
    node_count = serializers.SerializerMethodField()
    node_stat = serializers.SerializerMethodField()
    estimate_consume_time = serializers.SerializerMethodField()
    need_snapshot = serializers.SerializerMethodField()
    attacker_list = serializers.SerializerMethodField()

    def get_tag(self, obj):
        return  obj.tags

    def get_has_file(self, obj):
        return bool(obj.file)

    # 可获取的file 非debug模式内置资源不允许访问file
    def get_env_file(self, obj):
        if settings.DEBUG or not obj.builtin:
            env_file = obj.file
        else:
            env_file = None
        return serializers.FileField().to_representation(env_file)

    def get_vis_config(self, obj):
        try:
            return json.dumps(resource_util.convert_json_config(json.loads(obj.json_config)), cls=DjangoJSONEncoder)
        except:
            return None

    def get_node_stat(self, obj):
        memory = 0
        disk = 0
        for envterminal in obj.envterminal_set.all():
            flavor = envterminal.flavor
            if flavor:
                details = flavor.split('-')
                try:
                    m = float(details[-2][:-1])
                except:
                    m = 1
                try:
                    d = float(details[-1][:-1])
                except:
                    d = 10
            else:
                m = 1
                d = 10
            memory += m
            disk += d

        return {
            'memory': memory,
            'disk': disk,
        }

    def get_node_count(self, obj):
        return {
            'terminal': env_models.EnvTerminal.objects.filter(env=obj).count(),
            'gateway': env_models.EnvGateway.objects.filter(env=obj).count(),
            'network': env_models.EnvNet.objects.filter(env=obj).count(),
        }

    def get_estimate_consume_time(self, obj):
        return Getter.get_estimate_env_consume_time(obj.json_config)

    def get_need_snapshot(self, obj):
        return env_models.EnvTerminal.objects.filter(env=obj).exclude(Q(install_script=None) | Q(install_script='')).exists()

    def get_attacker_list(self, obj):
        if not obj.attackers:
            return []
        envattackers = env_models.EnvAttacker.objects.filter(id__in=json.loads(obj.attackers))
        return EnvAttackerSerializer(envattackers, many=True).data

    def _get_request_env_file(self):
        return self.context['request'].data.get('env_file')

    def _parse_json_config(self, data):
        json_config = None
        # source_flag json_config来源 0未解析到 1直接传入 2从vis_config 3从资源文件
        source_flag = 0

        # 优先解析json_config
        json_config = data.get('json_config')
        if json_config:
            source_flag = 1
        else:
            # 然后解析资源zip文件中的config.json
            env_file = data.get('file')
            if env_file:
                json_config = resource_util.read_json_config_from_file(env_file)
                if json_config:
                    source_flag = 3

        # 最后解析vis_config
        if not json_config:
            request = self.context['request']
            vis_config = request.data.get('vis_config')
            if vis_config:
                try:
                    vis_config = json.loads(vis_config)
                except:
                    pass
                else:
                    json_config = json.dumps(resource_util.convert_vis_config(vis_config))
                    if json_config:
                        source_flag = 2

        # 检查json可解析
        if json_config:
            json.loads(json_config)

        return json_config, source_flag

    def _fix_attackers(self, validated_data):
        if 'attackers' not in validated_data:
            return

        attackers = validated_data.get('attackers')
        if not attackers:
            return

        try:
            attackers = json.loads(attackers)
            if not isinstance(attackers, list):
                raise Exception()
        except:
            validated_data.pop('attackers')
            return

        envattackers = env_models.EnvAttacker.objects.filter(id__in=attackers)
        attackers = [envattacker.id for envattacker in envattackers]
        validated_data['attackers'] = json.dumps(attackers)

    def create(self, validated_data):
        self._fix_attackers(validated_data)

        try:
            json_config, source_flag = self._parse_json_config(validated_data)
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})
        if not json_config:
            raise exceptions.ValidationError({'json_config': error.NO_ENV_CONFIG})

        name = validated_data.get('name')
        need_merge = source_flag in [1, 2]
        # 名称改变合并进文件
        try:
            config_data = json.loads(json_config)
            config_name = config_data['scene']['name']
            if name and name != config_name:
                config_data['scene']['name'] = name
                json_config = json.dumps(config_data)
                need_merge = True
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})

        # 已经存在的用户不能添加
        name = name or config_name
        if env_models.Env.objects.filter(status=env_models.Env.Status.TEMPLATE, name=name).exists():
            raise exceptions.ValidationError({'json_config': [error.ENV_NAME_EXISTS]})

        # 需要合并json_config到资源文件
        env_file = validated_data.get('file')
        if not env_file:
            env_file = resource_util.empty_zip_file()
            validated_data['file'] = env_file

        if need_merge:
            try:
                validated_data['file'] = resource_util.merge_config_to_file(env_file, json_config)
            except Exception as e:
                raise exceptions.ValidationError({'file': e.message})

        request = self.context['request']
        # handler处理json_config
        validated_data.pop('json_config', None)
        # 创建环境模板
        try:
            handler = EnvConfigHandler(user=request.user, config=json_config)
            env = handler.create_env_template(**validated_data)
        except MsgException as e:
            raise exceptions.ValidationError({'json_config': e.message})

        # 解压攻防文件
        if env.type == env_models.Env.Type.ATTACK_DEFENSE:
            resource_util.extract_env_file(env)

        return env

    def update(self, instance, validated_data):
        self._fix_attackers(validated_data)
        try:
            json_config, source_flag = self._parse_json_config(validated_data)
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})

        name = validated_data.get('name') or instance.name
        env_file = validated_data.get('file')
        need_merge = (json_config or env_file) and source_flag != 3 and not (json_config and json_config == instance.json_config and not env_file)
        # 名称改变合并进文件
        try:
            config_data = json.loads(json_config or instance.json_config)
            config_name = config_data['scene']['name']
            if name and name != config_name:
                config_data['scene']['name'] = name
                json_config = json.dumps(config_data)
                need_merge = True
        except Exception as e:
            raise exceptions.ValidationError({'json_config': e.message or 'invalid config'})

        # 需要合并json_config到资源文件
        if need_merge:
            merging_json_config = json_config or instance.json_config
            merging_env_file = env_file or instance.file or resource_util.empty_zip_file()
            try:
                validated_data['file'] = resource_util.merge_config_to_file(merging_env_file, merging_json_config)
            except Exception as e:
                raise exceptions.ValidationError({'file': e.message})

        request = self.context['request']
        # handler处理json_config
        validated_data.pop('json_config', None)
        # 更新结构
        if json_config:
            try:
                handler = EnvConfigHandler(user=request.user, config=json_config)
                handler.update_env_template(instance, **validated_data)
            except MsgException as e:
                raise exceptions.ValidationError({'json_config': e.message})
        # 普通更新
        else:
            for field_name, value in validated_data.items():
                setattr(instance, field_name, value)
            instance.save()

        # 解压攻防文件 需要解压的条件 类型更新为攻防或攻防文件更新了
        if validated_data.get('type') == env_models.Env.Type.ATTACK_DEFENSE or (instance.type == env_models.Env.Type.ATTACK_DEFENSE and validated_data.get('file')):
            resource_util.extract_env_file(instance)

        return instance

    def to_internal_value(self, data):
        internal_data = super(EnvSerializer, self).to_internal_value(data)
        env_file = self._get_request_env_file()
        if env_file:
            env_file.name = '%s.zip' % uuid.uuid4()
            internal_data['file'] = env_file
        return internal_data


    class Meta:
        model = env_models.Env
        if settings.DEBUG:
            fields = ('id', 'type', 'has_file', 'env_file', 'json_config', 'image_status', 'modify_time', 'builtin', 'attackers', 'attacker_list',
                      'name', 'desc', 'vulns', 'tools', 'tag', 'vis_config', 'node_count', 'node_stat', 'estimate_consume_time', 'need_snapshot',
                      'creater_username', 'is_other_share', 'share', 'share_count')
        else:
            fields = ('id', 'type', 'has_file', 'env_file', 'image_status', 'modify_time', 'builtin', 'attackers', 'attacker_list',
                      'name', 'desc', 'vulns', 'tools', 'tag', 'vis_config', 'node_count', 'node_stat', 'estimate_consume_time', 'need_snapshot',
                      'creater_username', 'is_other_share', 'share', 'share_count')
        read_only_fields = ('desc', 'vulns', 'tools')


class StandardDeviceEditServerSerializer(serializers.ModelSerializer):
    proxy_ip = serializers.SerializerMethodField()
    connection_url = serializers.SerializerMethodField()

    def get_proxy_ip(self, obj):
        return proxy.PROXY_IP if proxy.PROXY_SWITCH else None

    def get_connection_url(self, obj):
        return RemoteManager(server=obj.host_ip).get_connection_url(obj.connection_id) if obj.connection_id else ''

    class Meta:
        model = env_models.StandardDeviceEditServer
        fields = ('id', 'connection_url', 'status', 'protocol', 'float_ip', 'port', 'proxy_ip', 'proxy_port', 'username', 'password')


class StandardDeviceSerializer(serializers.ModelSerializer,
                               common_serializers.BaseShareSerializer,
                               common_serializers.CreateUserNameAndShareSerializer):
    loaded_lan_configs = serializers.SerializerMethodField()
    tmp_vm_info = serializers.SerializerMethodField()
    loaded_meta_data = serializers.SerializerMethodField()
    _terminal_null_fields = (
        'image_type',
        'system_type',
        'system_sub_type',
        'source_image_name',
        'disk_format',
        'meta_data',
        'tmp_vm',
        'flavor',
        'access_mode',
        'access_port',
        'access_connection_mode',
        'access_user',
        'access_password',
    )

    def get_loaded_lan_configs(self, obj):
        lan_configs = obj.lan_configs
        if lan_configs:
            return json.loads(lan_configs)
        else:
            return {}

    def get_tmp_vm_info(self, obj):
        return StandardDeviceEditServerSerializer(obj.tmp_vm).data if obj.tmp_vm else None

    def get_loaded_meta_data(self, obj):
        meta_data = obj.meta_data
        if meta_data:
            return json.loads(meta_data)
        else:
            return {}

    def to_internal_value(self, data):
        data_filter = DataFilter(data)
        if data.get('image_type'):
            image_type = data_filter.get('image_type', env_models.StandardDevice.ImageType.values())
            if not image_type:
                raise exceptions.ValidationError({'image_type': [error.INVALID_VALUE]})
        if data.get('system_type'):
            system_type = data_filter.get('system_type', env_models.StandardDevice.SystemType.values())
            if not system_type:
                raise exceptions.ValidationError({'system_type': [error.INVALID_VALUE]})

        if data.get('system_sub_type'):
            system_sub_type = data_filter.get('system_sub_type', env_models.StandardDevice.SystemSubType.values())
            if not system_sub_type:
                raise exceptions.ValidationError({'system_sub_type': [error.INVALID_VALUE]})
            data._mutable = True
            data['system_type'] = env_models.StandardDevice.SystemSubTypeMap[system_sub_type]
            data._mutable = False

        if data.get('flavor'):
            flavor = data_filter.get('flavor', api_settings.FLAVORS)
            if not flavor:
                raise exceptions.ValidationError({'flavor': [error.INVALID_VALUE]})
        if data.get('access_mode'):
            access_mode = data_filter.get('access_mode', [
                env_models.EnvTerminal.AccessMode.SSH,
                env_models.EnvTerminal.AccessMode.RDP,
                env_models.EnvTerminal.AccessMode.TELNET,
                env_models.EnvTerminal.AccessMode.CONSOLE,
            ])
            if not access_mode:
                raise exceptions.ValidationError({'access_mode': [error.INVALID_VALUE]})
            if data.get('access_port'):
                if access_mode != env_models.EnvTerminal.AccessMode.RDP:
                    data._mutable = True
                    data['access_connection_mode'] = None
                    data._mutable = False

        logo = data.get('logo')
        default_logo = None
        if logo and isinstance(logo, (six.string_types, six.text_type)):
            default_logo_path = os.path.join(api_settings.FULL_DEFAULT_DEVICE_LOGO_DIR, logo)
            if os.path.exists(default_logo_path):
                data._mutable = True
                default_logo = logo
                data.pop('logo')
                data._mutable = False
        ret = super(StandardDeviceSerializer, self).to_internal_value(data)
        if default_logo:
            ret['logo'] = os.path.join(api_settings.DEFAULT_DEVICE_LOGO_DIR, default_logo)

        if data.get('meta_data'):
            meta_data_str = data.get('meta_data')
            try:
                meta_data = json.loads(meta_data_str)
            except Exception as e:
                raise exceptions.ValidationError({'meta_data': [error.INVALID_VALUE]})
            if not isinstance(meta_data, dict):
                raise exceptions.ValidationError({'meta_data': [error.INVALID_VALUE]})

        return ret

    # 文件上传比较大， 添加validate模式先验证基础数据
    def _validate_mode(self):
        request = self.context['request']
        return '_validate' in request.data

    def _terminal_mode(self, validated_data, instance=None):
        role = validated_data.get('role')
        role_type = validated_data.get('role_type')
        if instance:
            role = role or instance.role
            role_type = role_type or instance.role_type
        return role == env_models.StandardDevice.Role.TERMINAL \
                or (role == env_models.StandardDevice.Role.GATEWAY
                    and role_type not in (env_models.StandardDevice.RoleGatewayType.ROUTER, env_models.StandardDevice.RoleGatewayType.FIREWALL))

    def create(self, validated_data):
        name = validated_data.get('name')
        if name in api_settings.BASE_IMAGES:
            raise exceptions.ValidationError(error.CONFLICT_WITH_BASE_IMAGE_NAME)

        if env_models.StandardDevice.objects.filter(name=name).exists():
            raise exceptions.ValidationError({'name': [error.NAME_HAVE_EXISTED]})

        if not validated_data.get('logo'):
            raise exceptions.ValidationError(error.STANDARD_DEVICE_NO_LOGO)

        if self._terminal_mode(validated_data):
            # 上传模式
            if not validated_data.get('source_image_name'):
                if validated_data.get('disk_format') == 'docker':
                    validated_data['image_type'] = env_models.StandardDevice.ImageType.DOCKER
                else:
                    validated_data['image_type'] = env_models.StandardDevice.ImageType.VM
        else:
            [validated_data.update({field: None}) for field in self._terminal_null_fields]

        if self._validate_mode():
            return env_models.StandardDevice(**validated_data)
        else:
            return super(StandardDeviceSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.get('name')
        if name in api_settings.BASE_IMAGES:
            raise exceptions.ValidationError(error.CONFLICT_WITH_BASE_IMAGE_NAME)

        if name and name != instance.name and env_models.StandardDevice.objects.filter(name=name).exists():
            raise exceptions.ValidationError({'name': [error.NAME_HAVE_EXISTED]})

        if 'logo' in validated_data and validated_data['logo'] is None:
            validated_data.pop('logo')

        if not self._terminal_mode(validated_data, instance):
            [validated_data.update({field: None}) for field in self._terminal_null_fields]
        else:
            # 上传模式
            if not (validated_data.get('source_image_name') or instance.source_image_name):
                disk_format = validated_data.get('disk_format') or instance.disk_format
                if disk_format == 'docker':
                    validated_data['image_type'] = env_models.StandardDevice.ImageType.DOCKER
                else:
                    validated_data['image_type'] = env_models.StandardDevice.ImageType.VM
            # 已有镜像的情况不能更新基础镜像
            if instance.image_status == env_models.StandardDevice.ImageStatus.CREATED:
                validated_data.pop('source_image_name', None)

        if self._validate_mode():
            return instance
        else:
            return super(StandardDeviceSerializer, self).update(instance, validated_data)

    class Meta:
        model = env_models.StandardDevice
        fields = ('id', 'name', 'description', 'logo', 'role', 'role_type', 'wan_number', 'lan_number', 'lan_configs',
                  'image_type', 'system_type', 'system_sub_type', 'source_image_name', 'disk_format', 'meta_data', 'image_status', 'error', 'tmp_vm', 'tmp_vm_info',
                  'flavor', 'access_mode', 'access_port', 'access_connection_mode', 'access_user', 'access_password',
                  'init_support', 'hash', 'builtin', 'loaded_meta_data', 'loaded_lan_configs',
                  'creater_username', 'is_other_share', 'share', 'share_count')
        if settings.DEBUG:
            read_only_fields = ('error', 'tmp_vm',)
        else:
            read_only_fields = ('error', 'tmp_vm', 'image_status')


class EnvAttackerSerializer(serializers.ModelSerializer):
    creater_username = serializers.SerializerMethodField()

    def create(self, validated_data):
        request = self.context['request']
        config = request.data.get('config')
        if not config:
            raise exceptions.ValidationError({'config': error.NO_ATTACKER_CONFIG})

        try:
            handler = AttackerConfigHandler(user=request.user, config=config)
            attacker = handler.create(**validated_data)
        except MsgException as e:
            raise exceptions.ValidationError({'config': e.message})
        return attacker

    def update(self, instance, validated_data):
        request = self.context['request']
        config = request.data.get('config')
        if not config and validated_data:
            for field_name, value in validated_data.items():
                setattr(instance, field_name, value)
            instance.save()
            return instance

        try:
            handler = AttackerConfigHandler(user=request.user, config=config)
            attacker = handler.update(instance, **validated_data)
        except MsgException as e:
            raise exceptions.ValidationError({'config': e.message})
        return attacker

    def to_internal_value(self, data):
        data_filter = DataFilter(data)
        if data.get('type'):
            attacker_type = data_filter.get('type', env_models.EnvAttacker.Type.values())
            if not attacker_type:
                raise exceptions.ValidationError({'type': [error.INVALID_VALUE]})

        return super(EnvAttackerSerializer, self).to_internal_value(data)

    def get_creater_username(self, obj):
        if obj.create_user:
            return obj.create_user.first_name or obj.create_user.username
        else:
            return None

    class Meta:
        model = env_models.EnvAttacker
        fields = ('id', 'name', 'file', 'type', 'desc', 'json_config', 'creater_username')
        read_only_fields = ('json_config', )


class InstanceListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'server_name': row.get('name'),
            'server_ip': row.get('server_ip'),
            'server_status': row.get('status'),
            'create_time': row.get('create_time'),
            'node': row.get('node'),
            'create_user': row.get('create_user'),
            #'server_image': row.get('server_image'),

        }




class ImageDetailSerializer(object):
    def __init__(self, row):
        self.data = {
            'image_format': row.get('disk_format'),
            'id': row.get('image_id'),
            'image_name': row.get('name'),
            'image_protect': row.get('protected'),
            'image_vis': row.get('visable'),
            'image_size': row.get('size'),
            'image_create': row.get('upload_time'),
            'image_status': row.get('status'),
            # 'image_owner': row.get('owner'),

        }


class ImageListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'image_name': row.get('name'),
            'image_status': row.get('status'),
            'image_format': row.get('image_format'),
            'image_create': row.get('created_at'),
            'image_size': row.get('image_size'),
            'image_type': row.get('image_type'),
        }


class DockerListSerializer(object):
    def __init__(self, row):
        self.data = {
            'doc_image': row.get('image'),
            'doc_name': row.get('name'),
            'doc_status': row.get('status'),
            'id': row.get('id'),
            'node': row.get('host'),
            'address_list': row.get('address_list'),
            'create_user': row.get('create_user')


        }


class DockerImageListSerializer(object):
    def __init__(self, row):
        self.data = {
            'doc_image_id': row.get('image_id'),
            'doc_image_repo': row.get('image_repo'),
            'doc_image_size': row.get('image_size'),
            'doc_image_tag': row.get('image_tag'),
            'doc_image_uuid': row.get('image_uuid'),

        }


class NetListSerializer(object):
    def __init__(self, row):
        self.data = {
            'net_status': row.get('status'),
            'created_at': row.get('created_at'),
            'net_name': row.get('net_name'),
            'id': row.get('id'),
            'net_subnets': row.get('subnets'),
            'net_is_external': row.get('router:external'),
            'networkType': row.get('provider:network_type'),

        }


class RouterListSerializer(object):
    def __init__(self, row):
        self.data = {
            'route_status': row.get('status'),
            'route_name': row.get('name'),
            'id': row.get('id'),
            'created_at': row.get('created_at'),
        }


class FloatIpListSerializer(object):
    def __init__(self, row):
        self.data = {
            'float_status': row.get('status'),
            'float_created_at': row.get('created_at'),
            'fixed_ip_address': row.get('fixed_ip_address'),
            'float_ip_address': row.get('floating_ip_address'),
            'id': row.get('id'),
            # 'floating_network_id': row.get('floating_network_id'),


        }


class FwaasGroupListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'status': row.get('status'),
            'description': row.get('description'),
            'name': row.get('name'),
            'ingress_name': row.get('ingress_name'),
            'engress_name': row.get('engress_name'),
            'ingress_id': row.get('ingress_id'),
            'engress_id': row.get('engress_id'),

        }


class FwaasRuleListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'description': row.get('description'),
            'name': row.get('name'),
            'protocol': row.get('protocol'),
            'shared': row.get('shared'),
            'enabled': row.get('enabled'),
            'action': row.get('action'),
            'source_ip': row.get('source_ip_address'),
            'destination_ip': row.get('destination_ip_address'),
            'source_port': row.get('source_port'),
            'destination_port': row.get('destination_port'),
            'type': row.get('type'),
        }


class FwaasPolicyListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'description': row.get('description'),
            'audited': row.get('audited'),
            'name': row.get('name'),
            'shared': row.get('shared'),
            'firewall_rules': row.get('firewall_rules'),

        }
