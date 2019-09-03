# -*- coding: utf-8 -*-
import copy
import json
import jsonschema
import logging

from django.db import transaction
from django.utils import six, timezone
from django.utils.translation import ugettext_lazy as _

from common_framework.utils.enum import enum

from common_env.models import *
from common_env.setting import api_settings
from common_env.utils.permission import is_admin
from system_configuration.models import SystemConfiguration

from .error import error
from .exceptions import MsgException


logger = logging.getLogger(__name__)


PLATFORM_ID = 'platform'

INTERNET_NET_ID_PREFIX = 'internet'

IP_PATTERN_STR = r'(?:(?:2[0-4][0-9]\.)|(?:25[0-5]\.)|(?:1[0-9][0-9]\.)|(?:[1-9][0-9]\.)|(?:[0-9]\.)){3}(?:(?:2[0-5][0-5])|(?:25[0-5])|(?:1[0-9][0-9])|(?:[1-9][0-9])|(?:[0-9]))'

IP_PATTERN = r'^' + IP_PATTERN_STR + r'$'

IP_PATTERN_E = r'^(' + IP_PATTERN_STR + r')?$'

CIDR_PATTERN = r'^' + IP_PATTERN_STR + r'/\d+$'

CIDR_PATTERN_E = r'^(' + IP_PATTERN_STR + r'/\d+)?$'

IP_OR_CIDR_PATTERN = r'^' + IP_PATTERN_STR + r'(/\d+)?$'

IP_OR_CIDR_PATTERN_E = r'^(' + IP_PATTERN_STR + r'(/\d+)?)?$'

PORT_OR_RANGE_STR = r'[1-9]\d{0,}(:[1-9]\d{0,})?'

PORT_OR_RANGE_PATTERN_E = r'^(' + PORT_OR_RANGE_STR + ')?$'

IP_TYPE = enum(
    INNER_FIXED=0,
    OUTER_FIXED=1,
    FLOAT=2,
)


def is_internet(net_id):
    return net_id.lower().startswith(INTERNET_NET_ID_PREFIX)


class JsonConfigParser(object):
    def __init__(self, content=None, file=None):
        if content:
            if isinstance(content, (six.string_types, six.text_type)):
                self.raw_config = json.loads(content)
            elif isinstance(content, dict):
                self.raw_config = content
            else:
                raise Exception('invalid content type: %s' % type(content))
        else:
            if not file:
                raise Exception('empty config')

            if isinstance(file, (six.string_types, six.text_type)):
                with open(file, 'r') as f:
                    self.raw_config = json.loads(f.read())
            elif hasattr(file, 'read'):
                self.raw_config = json.loads(file.read())
            else:
                raise Exception('invalid file type: %s' % type(content))

        if not self.raw_config:
            raise Exception('empty config')

        self.config = None

    def schema_validate(self):
        try:
            jsonschema.validate(self.raw_config, self.schema)
        except jsonschema.ValidationError as e:
            attr_name = e.schema.get('name') or e.schema.get('description')
            message = '{}[{}]: {}'.format(_('x_invalid_value'), attr_name, e.instance)
            raise MsgException(message)

    def extra_validate(self):
        self.config = self.raw_config

    def get_config(self):
        if self.config:
            return self.config
        self.schema_validate()
        self.extra_validate()
        return self.config


# json schema验证配置
class JsonEnvConfigParser(JsonConfigParser):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "positiveInteger": {
                "minimum": 0,
                "type": "integer"
            },
            "positiveIntegerDefault0": {
                "allOf": [
                    {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    {
                        "default": 0
                    }
                ]
            },
            "schemaArray": {
                "items": {
                    "$ref": "#"
                },
                "minItems": 1,
                "type": "array"
            },
            "simpleTypes": {
                "enum": [
                    "array",
                    "boolean",
                    "integer",
                    "null",
                    "number",
                    "object",
                    "string"
                ]
            },
            "stringArray": {
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True
            },
            "emptyStringArray": {
                "items": {
                    "type": "string"
                },
                "type": "array",
                "uniqueItems": True
            }
        },
        "title": "题目环境拓扑",
        "description": "实现方式，先申请网络，每个虚拟机关联N个网络，网络之间需要互通，只需要申请一个路由器连接需要互通的路由器即可",
        "type": "object",
        "properties": {
            "scene": {
                "description": "虚拟场景申明",
                "type": "object",
                "properties": {
                    "name": {
                        "description": "场景名称",
                        "type": "string"
                    },
                    "desc": {
                        "description": "场景描述",
                        "type": "string"
                    },
                    "vulns": {
                        "description": "关联漏洞",
                        "$ref": "#/definitions/emptyStringArray"
                    },
                    "tools": {
                        "description": "关联工具",
                        "$ref": "#/definitions/emptyStringArray"
                    },
                    "tag": {
                        "description": "标签",
                        "$ref": "#/definitions/emptyStringArray"
                    }
                },
                "required": ["name"]
            },
            "networks": {
                "description": "虚拟网络申明",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "唯一id",
                            "type": "string",
                        },
                        "name": {
                            "description": "网络名称",
                            "type": "string"
                        },
                        "range": {
                            "name": "网段",
                            "description": "未填写将自动分配，1.1.1.0/24",
                            "type": "string",
                            "pattern": CIDR_PATTERN_E,
                        },
                        "gateway": {
                            "name": "网关",
                            "description": "未填写将自动分配254",
                            "type": "string",
                            "pattern": IP_PATTERN_E,
                        },
                        "dns": {
                            "name": "DNS",
                            "description": "未填写将自动分配",
                            "$ref": "#/definitions/emptyStringArray",
                            "pattern": IP_PATTERN_E,
                        },
                        "dhcp": {
                            "description": "dhcp",
                            "type": "boolean",
                        },

                    },
                    "required": ["id", "name"],
                    "minItems": 0,
                    "uniqueItems": True
                }
            },
            "routers": {
                "description": "虚拟路由申明",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "路由id",
                            "type": "string",
                        },
                        "name": {
                            "description": "路由名称",
                            "type": "string"
                        },
                        "net": {
                            "description": "路由网络列表",
                            "$ref": "#/definitions/emptyStringArray"
                        },
                        "staticRouting": {
                            "description": "静态路由表",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "destination": {
                                        "name": "静态路由目的地址",
                                        "description": "支持ip(1.1.1.1)或子网(1.1.1.0/24)",
                                        "type": "string",
                                        "pattern": IP_OR_CIDR_PATTERN,
                                    },
                                    "gateway": {
                                        "description": "静态路由下一跳地址",
                                        "type": "string",
                                        "pattern": IP_PATTERN,
                                    }
                                },
                                "required": ["destination", "gateway"],
                                "minItems": 0,
                                "uniqueItems": True
                            }
                        },
                        "canUserConfigure": {
                            "description": "是否支持用户侧配置",
                            "type": "boolean",
                        },
                    },
                },
                "minItems": 0,
                "uniqueItems": True
            },
            "firewalls": {
                "description": "防火墙申明",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "防火墙id",
                            "type": "string",
                        },
                        "name": {
                            "description": "防火墙名称",
                            "type": "string"
                        },
                        "net": {
                            "description": "防火墙网络列表",
                            "$ref": "#/definitions/emptyStringArray"
                        },
                        "staticRouting": {
                            "description": "静态路由表",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "destination": {
                                        "name": "静态路由目的地址",
                                        "description": "支持ip(1.1.1.1)或子网(1.1.1.0/24)",
                                        "type": "string",
                                        "pattern": IP_OR_CIDR_PATTERN,
                                    },
                                    "gateway": {
                                        "description": "静态路由下一跳地址",
                                        "type": "string",
                                        "pattern": IP_PATTERN,
                                    }
                                },
                                "required": ["destination", "gateway"],
                                "minItems": 0,
                                "uniqueItems": True
                            }
                        },
                        "rule": {
                            "description": "防火墙规则",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "protocol": {
                                        "name": "防火墙规则协议",
                                        "description": "必填，tcp/udp/icmp/any",
                                        "type": "string",
                                        "pattern": r"^tcp|udp|icmp|any$"
                                    },
                                    "action	": {
                                        "name": "防火墙规则类型",
                                        "description": "必填，allow/deny/reject",
                                        "type": "string",
                                        "pattern": r"^allow|deny|reject$"
                                    },
                                    "sourceIP": {
                                        "name": "防火墙规则源地址",
                                        "description": "选填，支持ip(1.1.1.1)或子网(1.1.1.0/24)，支持变量",
                                        "type": "string",
                                        "pattern": IP_OR_CIDR_PATTERN,
                                    },
                                    "destIP": {
                                        "name": "防火墙规则目的地址",
                                        "description": "选填，支持ip(1.1.1.1)或子网(1.1.1.0/24)，支持变量",
                                        "type": "string",
                                        "pattern": IP_OR_CIDR_PATTERN,
                                    },
                                    "sourcePort": {
                                        "name": "防火墙规则源端口",
                                        "description": "选填，支持单个prot或port range，支持变量",
                                        "type": "string",
                                        "pattern": PORT_OR_RANGE_PATTERN_E,
                                    },
                                    "destPort": {
                                        "name": "防火墙规则目的端口",
                                        "description": "选填，支持单个prot或port range，支持变量",
                                        "type": "string",
                                        "pattern": PORT_OR_RANGE_PATTERN_E,
                                    },
                                    "direction": {
                                        "name": "防火墙规则方向",
                                        "description": "选填，ingress/egress/both",
                                        "type": "string",
                                        "pattern": r"^$|ingress|egress|both$"
                                    },
                                },
                                "required": ["protocol", "action"],
                            }
                        },
                        "canUserConfigure": {
                            "description": "是否支持用户侧配置",
                            "type": "boolean",
                        },
                    },
                    "required": ["id", "name", "net"],
                },
                "minItems": 0,
                "uniqueItems": True
            },
            "servers": {
                "description": "虚拟机申明",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "虚拟机id",
                            "type": "string",
                        },
                        "name": {
                            "description": "虚拟机名称",
                            "type": "string"
                        },
                        "imageType": {
                            "name": "虚拟机镜像类型",
                            "description": "镜像类型 支持 docker|vm",
                            "type": "string",
                            "pattern": r"^docker|vm$"
                        },
                        "systemType": {
                            "name": "虚拟机系统类型",
                            "description": "系统类型 支持 linux|windows",
                            "type": "string",
                            "pattern": r"^linux|windows|other$"
                        },
                        "systemSubType": {
                            "name": "虚拟机系统详细类型",
                            "description": "系统详细类型",
                            "type": "string",
                            "pattern": r"^%s$" % '|'.join(EnvTerminal.SystemSubType.values()),
                        },
                        "image": {
                            "name": "虚拟机镜像",
                            "description": "镜像名称或编号，需检查为系统中存在系统",
                            "type": "string",
                        },
                        "flavor": {
                            "name": "虚拟机大小",
                            "description": "虚拟服务器大小",
                            "type": "string",
                            "pattern": r"^%s$" % '|'.join(api_settings.FLAVORS)
                        },
                        "role": {
                            "name": "虚拟机角色",
                            "description": "operator/target/wingman/gateway 在场景中的角色,操作机和靶机会分配float_ip",
                            "type": "string",
                            "pattern": r"^operator|target|wingman|gateway|executer$"
                        },
                        "wan_number": {
                            "name": "虚拟网关wan口数量",
                            "description": "wan口数量",
                            "$ref": "#/definitions/positiveIntegerDefault0"
                        },
                        "lan_number": {
                            "name": "虚拟网关lan口数量",
                            "description": "lan口数量",
                            "$ref": "#/definitions/positiveIntegerDefault0"
                        },
                        "external": {
                            "name": "外网是否需要直接访问",
                            "description": "外网是否需要直接访问，operator和target默认True，wingman默认False,会分配Floating_ip",
                            "type": "boolean",
                        },
                        "initScript": {
                            "name": "初始化脚本",
                            "description": "初始化文件，支持相对路径",
                            "type": "string",
                        },
                        "installScript": {
                            "name": "安装脚本",
                            "description": "安装脚本文件，支持相对路径",
                            "type": "string",
                        },
                        "deployScript": {
                            "name": "部署脚本",
                            "description": "部署脚本文件，支持相对路径",
                            "type": "string",
                        },
                        "cleanScript": {
                            "name": "清除脚本",
                            "description": "清除场景内容，支持相对路径",
                            "type": "string",
                        },
                        "pushFlagScript": {
                            "name": "推送flag脚本",
                            "description": "flag推送，支持相对路径",
                            "type": "string",
                        },
                        "checkScript": {
                            "name": "检查脚本",
                            "description": "检查脚本，支持相对路径",
                            "type": "string",
                        },
                        "attackScript": {
                            "name": "攻击脚本",
                            "description": "攻击脚本，支持相对路径",
                            "type": "string",
                        },
                        "checker": {
                            "name": "检查机器",
                            "description": "检查脚本的执行者id",
                            "type": "string",
                        },
                        "attacker": {
                            "name": "攻击机器",
                            "description": "攻击脚本的执行者id",
                            "type": "string",
                        },
                        "accessMode": {
                            "description": "常见可以用协议和端口",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "protocol": {
                                        "description": "接入协议",
                                        "type": "string",
                                    },
                                    "port": {
                                        "description": "接入端口",
                                        "oneOf": [{
                                            "type": "string",
                                            "pattern": r"^$",
                                        }, {
                                            "type": "integer"
                                        }]
                                    },
                                    "mode": {
                                        "name": "接入模式",
                                        "description": "连接模式, 暂时只有rdp有, rdp|nla",
                                        "type": "string",
                                        "pattern": r"^rdp|nla$"
                                    },
                                    "username": {
                                        "name": "接入用户",
                                        "description": "用户",
                                        "type": "string",
                                    },
                                    "password": {
                                        "name": "接入密码",
                                        "description": "密码",
                                        "type": "string",
                                    },
                                    "desc": {
                                        "name": "接入描述",
                                        "description": "描述",
                                        "type": "string",
                                    },
                                },
                                "required": ["protocol"],
                            },
                            "minItems": 0,
                            "uniqueItems": True
                        },
                        "installers": {
                            "description": "安装工具列表",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "description": "安装工具名称",
                                        "type": "string",
                                    },
                                    "version": {
                                        "description": "安装工具版本",
                                        "type": "string",
                                    },
                                },
                                "required": ["name"],
                            },
                            "minItems": 0,
                            "uniqueItems": True
                        },
                        "net": {
                            "description": "设备接入的网络",
                            "type": "array",
                            "items": {
                                "anyOf": [
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "description": "网络id",
                                            "type": "string",
                                        },
                                        "ip": {
                                            "description": "ip",
                                            "type": "string",
                                            "pattern": IP_PATTERN_E,
                                        },
                                        "netmask": {
                                            "description": "netmask",
                                            "type": "string",
                                            "pattern": IP_PATTERN_E,
                                        },
                                        "gateway": {
                                            "description": "gateway",
                                            "type": "string",
                                            "pattern": IP_PATTERN_E,
                                        },
                                        "egress": {
                                            "description": "egress",
                                            "anyOf": [{
                                                "type": "string",
                                                "pattern": r"^$",
                                            }, {
                                                "type": "number",
                                                "minimum": 0,
                                            }]
                                        },
                                        "ingress": {
                                            "description": "ingress",
                                            "anyOf": [{
                                                "type": "string",
                                                "pattern": r"^$",
                                            }, {
                                                "type": "number",
                                                "minimum": 0,
                                            }]
                                        }
                                    }
                                }
                            ]
                            },
                            "minItems": 0,
                            "uniqueItems": True
                        },
                    },
                    "required": ["id", "name", "imageType", "image", "role"],
                },
                "minItems": 0,
                "uniqueItems": True
            },
        },
        "required": ["scene"]
    }



# 环境配置处理， 生成环境模板
class EnvConfigHandler(object):
    def __init__(self, user, config=None, file=None):
        self.user = user
        try:
            if config:
                parser = JsonEnvConfigParser(config)
            elif file:
                parser = JsonEnvConfigParser(file=file)
            else:
                raise MsgException(error.NO_CONFIG)
            self.config = parser.get_config()
        except Exception as e:
            raise MsgException(e.message)

        self.is_admin = is_admin(user)

    @staticmethod
    def get_terminal_number_limit():
        system_configuration = SystemConfiguration.objects.filter(key='terminal_node_number').first()
        terminal_node_number = system_configuration.value.strip() if system_configuration else None
        try:
            terminal_node_number = int(terminal_node_number)
        except:
            terminal_node_number = 2
        return terminal_node_number

    def create_env_template(self, **env_extra_params):
        with transaction.atomic():
            scene = self.config['scene']

            params = {
                'user': self.user,
                'status': Env.Status.TEMPLATE,
                'json_config': json.dumps(self.config),
                'name': scene['name'],
                'desc': scene.get('desc', ''),
                'vulns': json.dumps(scene.get('vulns', [])),
                'tools': json.dumps(scene.get('tools', [])),
                'tags': json.dumps(scene.get('tag', [])),
            }
            params.update(env_extra_params)
            env = Env.objects.create(**params)
            self.generate_env_structure(env)

        return env

    def update_env_template(self, env, **env_extra_params):
        with transaction.atomic():
            # 重建场景结构
            self.rebuild_env_structure(env)
            # 更新场景信息
            scene = self.config['scene']
            env.name = scene['name']
            env.desc = scene.get('desc', '')
            env.vulns = json.dumps(scene.get('vulns', []))
            env.tools = json.dumps(scene.get('tools', []))
            env.tags = json.dumps(scene.get('tag', []))
            # update方法文件保存不了, 使用save
            env.json_config = json.dumps(self.config)
            env.modify_time = timezone.now()
            for field_name, value in env_extra_params.items():
                setattr(env, field_name, value)
            env.save()
        return env

    def generate_env_structure(self, env):
        envnets = self.generate_envnets(env)
        envnet_subid_id = {envnet.sub_id: envnet.id for envnet in envnets}
        envgateways = self.generate_envgateways(env, envnet_subid_id)
        envterminals = self.generate_envterminals(env, envnet_subid_id)

    # 对比config变化重建场景结构
    def rebuild_env_structure(self, env):
        new_config = self.config
        old_config = json.loads(env.json_config)

        envnets = EnvNet.objects.filter(env=env)
        net_changed = new_config.get('networks') != old_config.get('networks')
        if net_changed:
            envnets.delete()
            envnets = self.generate_envnets(env)
        envnet_subid_id = {envnet.sub_id: envnet.id for envnet in envnets}

        envgateways = EnvGateway.objects.filter(env=env)
        if net_changed or new_config.get('routers') != old_config.get('routers') \
                or new_config.get('firewalls') != old_config.get('firewalls'):
            envgateways.delete()
            envgateways = self.generate_envgateways(env, envnet_subid_id)

        envterminals = EnvTerminal.objects.filter(env=env)
        if net_changed or new_config.get('servers') != old_config.get('servers'):
            envterminals.delete()
            envterminals = self.generate_envterminals(env, envnet_subid_id)

    def generate_envnets(self, env):
        networks = self.config.get('networks', [])
        envnets = []
        sub_ids = []
        for network in networks:
            sub_id = network['id']
            if sub_id in sub_ids:
                raise MsgException(error.DUMPLICATE_NETWORK_ID.format(id=sub_id))
            sub_ids.append(sub_id)

            envnet = EnvNet.objects.create(
                env=env,
                sub_id=network['id'],
                name=network['name'],
                gateway=network.get('gateway') or '',
                dns=json.dumps(network.get('dns', [])),
                cidr=network.get('range') if not is_internet(network['id']) else ''
            )
            envnets.append(envnet)
        return envnets

    def generate_envgateways(self, env, envnet_subid_id):
        routers = self.config.get('routers', [])
        firewalls = self.config.get('firewalls', [])

        envgateways = []
        sub_ids = []
        def _create_envgateway(gateway, gtype):
            sub_id = gateway['id']

            # unique check
            if sub_id in sub_ids:
                raise MsgException(error.DUMPLICATE_GATEWAY_ID.format(id=sub_id))
            sub_ids.append(sub_id)

            # net valid check
            nets = gateway['net']
            invalid_nets = list(set(nets) - set(envnet_subid_id.keys()))
            if invalid_nets:
                raise MsgException(error.INVALID_GATEWAY_NETS.format(gateway_id=sub_id, nets=str(invalid_nets)))
            nets_ids = [envnet_subid_id[net] for net in nets]

            create_params = {
                'env': env,
                'type': gtype,
                'sub_id': gateway['id'],
                'name': gateway['name'],
                'static_routing': json.dumps(gateway.get('staticRouting', [])),
                'can_user_configure': gateway.get('canUserConfigure', False),
            }
            if gtype == EnvGateway.Type.FIREWALL:
                create_params.update({
                    'firewall_rule': json.dumps(firewall.get('rule', [])),
                })
            envgateway = EnvGateway.objects.create(**create_params)
            envgateway.nets.set(nets_ids)
            envgateways.append(envgateway)
        for router in routers:
            _create_envgateway(router, EnvGateway.Type.ROUTER)
        for firewall in firewalls:
            _create_envgateway(firewall, EnvGateway.Type.FIREWALL)
        return envgateways

    def generate_envterminals(self, env, envnet_subid_id):
        servers = self.config.get('servers', [])

        terminal_number_limit = self.get_terminal_number_limit()
        if terminal_number_limit != 0 and len(servers) > terminal_number_limit:
            raise MsgException(error.TERMINAL_NUMBER_LIMIT.format(terminal_number_limit=terminal_number_limit))

        # 攻防模式只有一台机器，最多一台check机器
        if env.type == Env.Type.ATTACK_DEFENSE:
            target_count = len([server for server in servers if server['role'] == EnvTerminal.Role.TARGET])
            executer_count = len([server for server in servers if server['role'] == EnvTerminal.Role.EXECUTER])
            if target_count != 1 or executer_count > 1:
                raise MsgException(error.AD_TERMINAL_NUMBER_LIMIT.format(target_limit=1, executer_limit=1))

        all_sub_ids = [server['id'] for server in servers]

        envterminals = []
        sub_ids = []
        for terminal in servers:
            # unique check
            sub_id = terminal['id']
            if sub_id in sub_ids:
                raise MsgException(error.DUMPLICATE_TERMINAL_ID.format(id=sub_id))
            sub_ids.append(sub_id)

            # checker attacker id check
            checker = terminal.get('checker')
            if checker and checker not in all_sub_ids:
                raise MsgException(error.CHECKER_TERMINAL_NOT_EXIST.format(terminal_id=checker))
            attacker = terminal.get('attacker')
            if attacker and attacker not in all_sub_ids:
                raise MsgException(error.ATTACKER_TERMINAL_NOT_EXIST.format(terminal_id=checker))

            # net valid check
            nets = copy.copy(terminal.get('net', []))
            net_configs = []
            net_subids = []
            for net in nets:
                if isinstance(net, dict):
                    net_configs.append(net)
                    net_subid = net['id']
                    if net_subid not in envnet_subid_id:
                        raise MsgException(error.INVALID_TERMINAL_NETS.format(terminal_id=sub_id, nets=str([net_subid])))
                    net_subids.append(net_subid)
                else:
                    net_subids.append(net)

            invalid_nets = list(set(net_subids) - set(envnet_subid_id.keys()))
            if invalid_nets:
                raise MsgException(error.INVALID_TERMINAL_NETS.format(terminal_id=sub_id, nets=str(invalid_nets)))

            nets_ids = [envnet_subid_id[net_subid] for net_subid in net_subids]
            system_type = terminal['systemType']
            system_sub_type = terminal.get('systemSubType', EnvTerminal.SystemSubType.OTHER)
            if system_sub_type != EnvTerminal.SystemSubType.OTHER:
                system_type = StandardDevice.SystemSubTypeMap[system_sub_type]
            access_modes = terminal.get('accessMode', [])
            envterminal = EnvTerminal.objects.create(
                env=env,
                sub_id=sub_id,
                name=terminal['name'],
                image_type=terminal['imageType'],
                system_type=system_type,
                system_sub_type=system_sub_type,
                image=terminal['image'],
                role=terminal['role'],
                flavor=terminal.get('flavor'),
                init_script=terminal.get('initScript'),
                install_script=terminal.get('installScript'),
                deploy_script=terminal.get('deployScript'),
                clean_script=terminal.get('cleanScript'),
                push_flag_script=terminal.get('pushFlagScript'),
                check_script=terminal.get('checkScript'),
                attack_script=terminal.get('attackScript'),
                checker=checker,
                attacker=attacker,
                raw_access_modes=json.dumps(access_modes),
                access_modes=json.dumps(access_modes),
                installers=json.dumps(terminal.get('installers', [])),
                wan_number=terminal.get('wan_number') or 0,
                lan_number=terminal.get('lan_number') or 0,
                external=terminal.get('external', True),
                net_configs=json.dumps(net_configs),
                status=EnvTerminal.Status.TEMPLATE,
            )
            envterminal.nets.set(nets_ids)

            if envterminal.external and not self.has_external_envnet(envterminal):
                raise MsgException(error.TERMINAL_CANNOT_ACCESS_EXTERNAL_NET.format(terminal=envterminal.name))

            envterminals.append(envterminal)

        return envterminals

    def has_external_envnet(self, envterminal):
        if envterminal.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
            return True

        for envnet in envterminal.nets.all():
            for envgateway in envnet.envgateway_set.all():
                if envgateway.nets.filter(sub_id__istartswith=INTERNET_NET_ID_PREFIX).exists():
                    return True
        return False


class JsonAttackerConfigParser(JsonConfigParser):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "definitions": {
            "positiveInteger": {
                "minimum": 0,
                "type": "integer"
            },
            "positiveIntegerDefault0": {
                "allOf": [
                    {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    {
                        "default": 0
                    }
                ]
            },
            "schemaArray": {
                "items": {
                    "$ref": "#"
                },
                "minItems": 1,
                "type": "array"
            },
            "simpleTypes": {
                "enum": [
                    "array",
                    "boolean",
                    "integer",
                    "null",
                    "number",
                    "object",
                    "string"
                ]
            },
            "stringArray": {
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True
            },
            "emptyStringArray": {
                "items": {
                    "type": "string"
                },
                "type": "array",
                "uniqueItems": True
            }
        },
        "title": "攻击事件机器",
        "description": "攻击事件机器配置",
        "type": "object",
        "properties": {
            "servers": {
                "description": "虚拟机申明",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "row_id": {
                            "description": "数据库id",
                            "$ref": "#/definitions/positiveInteger"
                        },
                        "id": {
                            "description": "唯一id",
                            "type": "string",
                        },
                        "name": {
                            "description": "服务器名称",
                            "type": "string"
                        },
                        "imageType": {
                            "description": "镜像类型 支持 docker|vm",
                            "type": "string",
                            "pattern": r"^docker|vm$"
                        },
                        "systemType": {
                            "description": "系统类型 支持 linux|windows",
                            "type": "string",
                            "pattern": r"^linux|windows$"
                        },
                        "image": {
                            "description": "镜像名称或编号，需检查为系统中存在系统",
                            "type": "string",
                        },
                        "flavor": {
                            "description": "虚拟服务器大小",
                            "type": "string",
                            "pattern": r"^%s$" % '|'.join(api_settings.FLAVORS)
                        },
                        "external": {
                            "description": "外网是否需要直接访问，operator和target默认True，wingman默认False,会分配Floating_ip",
                            "type": "boolean",
                        },
                        "initScript": {
                            "description": "初始化文件，支持相对路径",
                            "type": "string",
                        },
                        "installScript": {
                            "description": "安装脚本文件，支持相对路径",
                            "type": "string",
                        },
                        "attackScript": {
                            "description": "攻击脚本，支持相对路径",
                            "type": "string",
                        },
                        "attackIntensity": {
                            "description": "攻击强度，支持traffic、scale 两种控制模式",
                            "type": "object",
                            "properties": {
                                "type": {
                                    "description": "限制模式（流量限制模式,单位KB/s， 规模限制模式）",
                                    "type": "string",
                                    "pattern": r"traffic|scale",
                                },
                                "bandwidth": {
                                    "description": "带宽 单位KB/s",
                                    "oneOf": [{
                                        "type": "string",
                                        "pattern": r"^$",
                                    }, {
                                        "$ref": "#/definitions/positiveInteger"
                                    }]
                                },
                                "intensity": {
                                    "description": "端口",
                                    "type": "object",
                                    "properties": {
                                        "low": {
                                            "description": "低",
                                            "$ref": "#/definitions/positiveInteger"
                                        },
                                        "middle": {
                                            "description": "中",
                                            "$ref": "#/definitions/positiveInteger"
                                        },
                                        "high": {
                                            "description": "高",
                                            "$ref": "#/definitions/positiveInteger"
                                        },

                                    },
                                    "required": ["low", "middle", "high"],
                                },
                            },
                            "required": ["type", "intensity"],
                        },
                        "accessMode": {
                            "description": "常见可以用协议和端口",
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "protocol": {
                                        "description": "协议",
                                        "type": "string",
                                    },
                                    "port": {
                                        "description": "端口",
                                        "type": "integer",
                                    },
                                    "mode": {
                                        "description": "连接模式, 暂时只有rdp有, rdp|nla",
                                        "type": "string",
                                        "pattern": r"^rdp|nla$"
                                    },
                                    "username": {
                                        "description": "用户",
                                        "type": "string",
                                    },
                                    "password": {
                                        "description": "密码",
                                        "type": "string",
                                    },
                                    "desc": {
                                        "description": "描述",
                                        "type": "string",
                                    },
                                },
                                "required": ["protocol"],
                            },
                            "minItems": 0,
                            "uniqueItems": True
                        },
                    },
                    "required": ["id", "name", "imageType", "image"],
                },
                "minItems": 0,
                "uniqueItems": True
            },
        },
        "required": ["servers"]
    }


class AttackerConfigHandler(object):
    def __init__(self, user, config=None, file=None):
        self.user = user
        try:
            if config:
                parser = JsonAttackerConfigParser(config)
            elif file:
                parser = JsonAttackerConfigParser(file=file)
            else:
                raise MsgException(error.NO_CONFIG)
            self.config = parser.get_config()
        except Exception as e:
            raise MsgException(e.message)

        self.is_admin = is_admin(user)

    def create(self, **extra_params):
        attacker = EnvAttacker.objects.create(
            json_config=json.dumps(self.config),
            create_user=self.user,
            **extra_params
        )
        return attacker

    def update(self, attacker, **extra_params):
        attacker.json_config = json.dumps(self.config)
        for field_name, value in extra_params.items():
            setattr(attacker, field_name, value)
        attacker.save()
        return attacker

