# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

from common_auth.models import User, Team
from common_framework.models import Builtin, BaseShare

from common_framework.models import ExecutePool
from common_framework.utils.enum import enum
from common_framework.utils.models.manager import MyManager
from common_framework.utils.unique import generate_unique_key
from common_resource.base.model import Resource

from common_env import resource


# 标靶临时编辑模板机器
class StandardDeviceEditServer(models.Model):
    # 临时生成用于编辑的模板机器
    tmp_network_ids = models.TextField(default='[]')
    tmp_router_ids = models.TextField(default='[]')
    tmp_docker_id = models.CharField(max_length=100, null=True, default=None)
    tmp_vm_id = models.CharField(max_length=100, null=True, default=None)
    tmp_net_ports = models.TextField(default='[]')

    protocol = models.CharField(max_length=32, null=True, default=None)
    float_ip = models.CharField(max_length=32, null=True, default=None)
    host_ip = models.CharField(max_length=32, null=True, default=None)
    host_name = models.CharField(max_length=1024, default=None, null=True)
    port = models.CharField(max_length=32, default=None, null=True)
    proxy_port = models.CharField(max_length=32, default=None, null=True)
    username = models.CharField(max_length=100, null=True, default=None)
    password = models.CharField(max_length=100, null=True, default=None)
    # 1创建中 2启动中 3运行中
    Status = enum(
        DELETED=0,
        CREATING=1,
        STARTING=2,
        RUNNING=3,
    )
    status = models.PositiveIntegerField(default=Status.CREATING)
    # 用于在线编辑的guacamole连接id
    connection_id = models.CharField(max_length=100, null=True, default=None)
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


# 标靶
class StandardDevice(Resource, Builtin, BaseShare):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default='')
    logo = models.ImageField(upload_to='standard_device_logo', null=True, default=None)
    # 设备角色：网关，网络，终端
    Role = enum(
        NETWORK=1,
        GATEWAY=2,
        TERMINAL=3,
    )
    role = models.PositiveIntegerField()
    RoleNetworkType = enum(
        NETWORK=1,
    )
    RoleGatewayType = enum(
        ROUTER=1,
        FIREWALL=2,
        TERMINAL_ROUTER=3,
        TERMINAL_FIREWALL=4,
        WAF=5,
        IPS=6,
        IDS=7,
    )
    RoleTerminalType = enum(
        OTHER=0,
        WEB_SERVER=1,
        DATABASE_SERVER=2,
        FILE_SERVER=3,
        BINARY_SERVER=4,
        MAIL_SERVER=5,
        OFFICE_EQUIPMENT=6,
        MOBILE_EQUIPMENT=7,
        INDUSTRIAL_CONTROL_EQUIPMENT=8,
        INTELLIGENT_EQUIPMENT=9,
        UAV=10,
    )
    RoleType = {
        Role.NETWORK: RoleNetworkType,
        Role.GATEWAY: RoleGatewayType,
        Role.TERMINAL: RoleTerminalType,
    }
    role_type = models.PositiveIntegerField()
    is_real = models.BooleanField(default=False)

    # -- 虚拟路由属性 --
    wan_number = models.PositiveIntegerField(default=0)
    lan_number = models.PositiveIntegerField(default=0)
    lan_configs = models.TextField(default='[]')

    # -- 虚拟终端属性 --
    # 镜像类型
    ImageType = enum(
        VM='vm',
        DOCKER='docker',
    )
    image_type = models.CharField(max_length=100, null=True, default=None)
    # 系统类型
    SystemType = enum(
        LINUX='linux',
        WINDOWS='windows',
        OTHER='other',
    )
    system_type = models.CharField(max_length=100, null=True, default=None)
    # 系统二级类型
    SystemSubType = enum(
        KALI_2='kali-2',
        UBUNTU_12='ubuntu-12',
        UBUNTU_14='ubuntu-14',
        UBUNTU_16='ubuntu-16',
        CENTOS_7='centos-7',
        CENTOS_6='centos-6',
        CENTOS_5='centos-5',
        WINDOWS_XP='windows-xp',
        WINDOWS_7='windows-7',
        WINDOWS_8='windows-8',
        WINDOWS_10='windows-10',
        WINDOWS_SERVER_2012='windows-server-2012',
        WINDOWS_SERVER_2008='windows-server-2008',
        WINDOWS_SERVER_2003='windows-server-2003',
        WINDOWS_SERVER_2000='windows-server-2000',
        ANDROID='android',
        UBUNTUKYLIN_18='ubuntukylin-18',
        OPENSOLARIS_11='opensolaris-11',
        OPENSUSE_LEAP_42='opensuse-leap-42',
        DEBIAN_9='debian-9',
        DEEPOFIX='deepofix',
        REDHAT_7='redhat-7',
        BACKTRACK_5='backtrack-5',
        OTHER='other',
    )
    SystemSubTypeMap = {
        SystemSubType.KALI_2: SystemType.LINUX,
        SystemSubType.UBUNTU_12: SystemType.LINUX,
        SystemSubType.UBUNTU_14: SystemType.LINUX,
        SystemSubType.UBUNTU_16: SystemType.LINUX,
        SystemSubType.CENTOS_7: SystemType.LINUX,
        SystemSubType.CENTOS_6: SystemType.LINUX,
        SystemSubType.CENTOS_5: SystemType.LINUX,
        SystemSubType.WINDOWS_XP: SystemType.WINDOWS,
        SystemSubType.WINDOWS_7: SystemType.WINDOWS,
        SystemSubType.WINDOWS_8: SystemType.WINDOWS,
        SystemSubType.WINDOWS_10: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2012: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2008: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2003: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2000: SystemType.WINDOWS,
        SystemSubType.ANDROID: SystemType.LINUX,
        SystemSubType.UBUNTUKYLIN_18: SystemType.LINUX,
        SystemSubType.OPENSOLARIS_11: SystemType.LINUX,
        SystemSubType.OPENSUSE_LEAP_42: SystemType.LINUX,
        SystemSubType.DEBIAN_9: SystemType.LINUX,
        SystemSubType.DEEPOFIX: SystemType.LINUX,
        SystemSubType.REDHAT_7: SystemType.LINUX,
        SystemSubType.BACKTRACK_5: SystemType.LINUX,
        SystemSubType.OTHER: SystemType.OTHER,
    }
    system_sub_type = models.CharField(max_length=100, null=True, default=SystemSubType.OTHER)
    # 来源基础镜像
    source_image_name = models.CharField(max_length=100, null=True, default=None)
    # 镜像格式(上传)
    disk_format = models.CharField(max_length=100, null=True, default=None)
    # 镜像元数据
    meta_data = models.TextField(null=True, default=None)
    # 镜像大小 对应EnvTerminal.Flavor
    flavor = models.CharField(max_length=100, null=True, default=None)
    # 默认访问方式 对应EnvTerminal.AccessMode
    access_mode = models.CharField(max_length=100, null=True, default=None)
    # 默认访问端口
    access_port = models.CharField(max_length=32, default=None, null=True)
    # 默认连接模式 目前只针对rdp的guacamole连接的rdp/nla
    access_connection_mode = models.CharField(max_length=100, null=True, default=None)
    # 默认访问用户 对应EnvTerminal.AccessMode
    access_user = models.CharField(max_length=100, null=True, default=None)
    # 默认访问密码 对应EnvTerminal.AccessMode
    access_password = models.CharField(max_length=256, null=True, default=None)
    # 是否支持初始化
    init_support = models.BooleanField(default=False)
    # 镜像状态
    ImageStatus = enum(
        NOT_APPLY=0,
        CREATING=1,
        CREATED=2,
        ERROR=3,
    )
    image_status = models.PositiveIntegerField(default=ImageStatus.NOT_APPLY)
    error = models.CharField(max_length=2048, default=None, null=True)
    # 临时编辑的模板机器
    tmp_vm = models.ForeignKey(StandardDeviceEditServer, on_delete=models.SET_NULL, null=True)

    hash = models.CharField(max_length=100, default=generate_unique_key)
    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.IntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, default=1,
                                    related_name='standard_device_create_user')
    modify_time = models.DateTimeField(default=timezone.now)
    modify_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='standard_device_modify_user')
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    class MyMeta:
        _builtin_modify_field = []

    ResourceMeta = resource.StandardDeviceMeta


# # snapshot
# class StandardDeviceSnapshot(models.Model):
#     standard_device = models.ForeignKey(StandardDevice)
#     name = models.CharField(max_length=128)
#     desc = models.CharField(max_length=1024, default='')
#     create_time = models.DateTimeField(default=timezone.now)


class Env(Resource, Builtin, BaseShare):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='env_create_user')
    team = models.ForeignKey(Team, null=True, default=None, on_delete=models.SET_NULL)
    Type = enum(
        BASE=1,
        ATTACK_DEFENSE=2,
    )
    type = models.PositiveIntegerField(default=Type.BASE)
    file = models.FileField(upload_to='env', null=True, default=None)
    json_config = models.TextField(default='{}')

    # info from json
    name = models.CharField(max_length=100, default=None, null=True)
    desc = models.TextField(default='')
    vulns = models.TextField(default='[]')
    tools = models.TextField(default='[]')
    tags = models.TextField(default='[]')

    # 被外部引用的关系
    hang_info = models.TextField(default='{}')

    attackers = models.TextField(default='[]')

    Status = enum(
        TEMPLATE=-1,
        DELETED=0,
        CREATING=1,
        USING=2,
        PAUSE=3,
        ERROR=4
    )
    UsingStatusList = (Status.USING, Status.PAUSE)
    ActiveStatusList = (Status.CREATING, Status.USING, Status.PAUSE)
    UseStatusList = (Status.CREATING, Status.USING, Status.PAUSE, Status.ERROR)
    AllStatusList = (Status.DELETED, Status.CREATING, Status.USING, Status.PAUSE, Status.ERROR)
    status = models.IntegerField(default=Status.CREATING)
    # 记录环境创建流程日志
    log = models.TextField(default='[]')
    # 记录环境出错信息
    error = models.CharField(max_length=2048, default=None, null=True)
    # 环境申请模板状态
    ImageStatus = enum(
        NOT_APPLY=0,
        CREATING=1,
        CREATED=2,
        ERROR=3,
    )
    image_status = models.IntegerField(default=ImageStatus.NOT_APPLY)

    # 环境创建时间
    create_time = models.DateTimeField(default=timezone.now)
    # 环境创建完成时间
    created_time = models.DateTimeField(default=None, null=True)
    # 环境创建消耗时间
    consume_time = models.PositiveIntegerField(default=0)
    # 环境暂停时间
    pause_time = models.DateTimeField(default=None, null=True)
    # 修改时间
    modify_time = models.DateTimeField(default=timezone.now)

    class MyMeta:
        _builtin_modify_field = []

    @property
    def is_attack_defense(self):
        if self.type == self.Type.ATTACK_DEFENSE:
            return True
        return False

    ResourceMeta = resource.EnvMeta


# 场景快照和生成环境对应关系
class SnapshotEnvMap(models.Model):
    # 环境模板
    template_env = models.ForeignKey(Env, on_delete=models.PROTECT, related_name='snapshot_env_map_template_env')
    # 用于创建快照的临时环境
    tmp_env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True, related_name='snapshot_env_map_tmp_env')


# 单独的测试场景
class TestEnvMap(models.Model):
    # 环境模板
    template_env = models.ForeignKey(Env, on_delete=models.PROTECT, related_name='test_env_map_template_env')
    # 用于测试场景的临时环境
    test_env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True, related_name='test_env_map_tmp_env')


class EnvNet(Resource, models.Model):
    env = models.ForeignKey(Env, on_delete=models.PROTECT)
    Type = StandardDevice.RoleNetworkType
    type = models.PositiveIntegerField(default=Type.NETWORK)
    sub_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default=None, null=True)
    cidr = models.CharField(max_length=1024, default=None, null=True)
    gateway = models.CharField(max_length=1024, default=None, null=True)
    dns = models.CharField(max_length=1024, default=None, null=True)
    dhcp = models.BooleanField(default=True)
    # from ecloud
    net_id = models.CharField(max_length=50, default=None, null=True)
    subnet_id = models.CharField(max_length=50, default=None, null=True)

    class Meta:
        unique_together = ('env', 'sub_id')

    ResourceMeta = resource.EnvNetMeta


class EnvGateway(Resource, models.Model):
    env = models.ForeignKey(Env, on_delete=models.PROTECT)
    Type = StandardDevice.RoleGatewayType
    type = models.PositiveIntegerField(default=Type.ROUTER)
    sub_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default=None, null=True)
    nets = models.ManyToManyField(EnvNet)

    # 路由器/防火墙属性
    router_id = models.CharField(max_length=50, default=None, null=True)
    static_routing = models.TextField(default='')
    # 防火墙属性
    firewall_rule = models.TextField(default='')
    firewall_id = models.CharField(max_length=50, default=None, null=True)
    can_user_configure = models.BooleanField(default=False)

    class Meta:
        unique_together = ('env', 'sub_id')

    ResourceMeta = resource.EnvGatewayMeta


class EnvTerminal(Resource, models.Model):
    env = models.ForeignKey(Env, on_delete=models.PROTECT, default=None, null=True)
    Type = StandardDevice.RoleTerminalType
    type = models.PositiveIntegerField(default=Type.OTHER)
    # open as vm_id for query
    sub_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default=None, null=True)
    nets = models.ManyToManyField(EnvNet)

    # 虚拟服务器属性
    SystemType = StandardDevice.SystemType
    system_type = models.CharField(max_length=100, default=SystemType.LINUX)
    SystemSubType = StandardDevice.SystemSubType
    system_sub_type = models.CharField(max_length=100, default=SystemSubType.OTHER)
    ImageType = StandardDevice.ImageType
    image_type = models.CharField(max_length=100, default=ImageType.VM)
    image = models.CharField(max_length=100)
    Role = enum(
        OPERATOR='operator',
        TARGET='target',
        WINGMAN='wingman',
        GATEWAY='gateway',
        EXECUTER='executer',
    )
    role = models.CharField(max_length=100, default=Role.TARGET)
    flavor = models.CharField(max_length=100, default=None, null=True)
    custom_script = models.CharField(max_length=2048, default=None, null=True)
    init_script = models.CharField(max_length=2048, default=None, null=True)
    install_script = models.CharField(max_length=2048, default=None, null=True)
    deploy_script = models.CharField(max_length=2048, default=None, null=True)
    clean_script = models.CharField(max_length=2048, default=None, null=True)
    push_flag_script = models.CharField(max_length=2048, default=None, null=True)
    check_script = models.CharField(max_length=2048, default=None, null=True)
    attack_script = models.CharField(max_length=2048, default=None, null=True)
    checker = models.CharField(max_length=100, default=None, null=True)
    attacker = models.CharField(max_length=100, default=None, null=True)
    wan_number = models.PositiveIntegerField(default=0)
    lan_number = models.PositiveIntegerField(default=0)
    external = models.BooleanField(default=True)
    net_configs = models.TextField(default='[]')
    AccessMode = enum(
        HTTP='http',
        HTTPS='https',
        NC='nc',
        SSH='ssh',
        RDP='rdp',
        CONSOLE='console',
        TELNET='telnet'
    )
    AccessModeDefaultPort = {
        AccessMode.HTTP: 80,
        AccessMode.HTTPS: 443,
        AccessMode.NC: 9999,
        AccessMode.SSH: 22,
        AccessMode.RDP: 3389,
        AccessMode.TELNET: 23,
    }
    raw_access_modes = models.TextField(default='[]')
    access_modes = models.TextField(default='[]')
    installers = models.TextField(default='[]')
    # 是否是攻击事件机器，攻击事件机器附属于攻击事件而不是场景
    is_attacker = models.BooleanField(default=False)
    AttackIntensityType = enum(
        TRAFFIC='traffic',
        SCALE='scale',
    )
    attack_intensity = models.TextField(default='{}')

    Status = enum(
        TEMPLATE=-1,
        DELETED=0,
        CREATING=1,
        CREATED=2,
        HATCHING=3,
        HATCHED=4,
        STARTING=5,
        STARTED=6,
        DEPLOYING=7,
        RUNNING=8,
        PAUSE=9,
        ERROR=10,
    )
    UsingStatusList = (Status.RUNNING, Status.PAUSE)
    status = models.IntegerField(default=Status.CREATING)
    # from ecloud, not open
    vm_id = models.CharField(max_length=50, default=None, null=True)
    policies = models.TextField(default='[]')
    net_ports = models.TextField(default='[]')
    fixed_ip = models.CharField(max_length=32, default=None, null=True)
    float_ip = models.CharField(max_length=32, default=None, null=True)
    host_ip = models.CharField(max_length=32, default=None, null=True)
    host_name = models.CharField(max_length=1024, default=None, null=True)
    # {"http:80": 12309, "ssh:22": 23543}
    proxy_port = models.TextField(default='{}')

    # 机器模板状态
    ImageStatus = enum(
        NOT_APPLY=0,
        CREATING=1,
        CREATED=2,
        ERROR=3,
    )
    image_status = models.PositiveIntegerField(default=ImageStatus.NOT_APPLY)
    # 机器模板
    image_id = models.CharField(max_length=100, null=True, default=None)

    # 机器创建时间
    create_time = models.DateTimeField(default=timezone.now)
    # 机器创建完成时间
    created_time = models.DateTimeField(default=None, null=True)
    # 机器创建消耗时间
    consume_time = models.PositiveIntegerField(default=0)
    # 机器暂停时间
    pause_time = models.DateTimeField(default=None, null=True)

    # 创建server参数用于重建
    create_params = models.TextField(default='{}')
    # 浮动ip参数用于重建
    float_ip_params = models.TextField(default='{}')
    # flags
    flags = models.TextField(default='[]')

    class Meta:
        unique_together = ('env', 'sub_id')

    ResourceMeta = resource.EnvTerminalMeta


class EnvAttacker(Resource, Builtin):
    name = models.CharField(max_length=100, unique=True)
    Type = enum(
        OBFUSCATION_FLOW=1,
        SNIFFING_DECEPTION=2,
        WEB_APPLICATION_PENETRATION=3,
        REMOTE_SERVICE_ATTACK=4,
        CLIENT_ATTACK=5,
        PASSWORD_CRACKING=6,
        DENIAL_OF_SERVICE=7,
        SOCIAL_ENGINEERING=8,
        WIRELESS_ATTACK=9,
    )
    type = models.PositiveIntegerField(default=Type.OBFUSCATION_FLOW)
    desc = models.TextField(default='')
    file = models.FileField(upload_to='envattacker', null=True, default=None)
    json_config = models.TextField(default='{}')
    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.IntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    ResourceMeta = resource.EnvAttackerMeta


class EnvAttackerInstance(models.Model):
    envattacker = models.ForeignKey(EnvAttacker, on_delete=models.SET_NULL, default=None, null=True)
    attach_env = models.ForeignKey(Env, on_delete=models.SET_NULL, default=None, null=True)
    attach_net = models.ForeignKey(EnvNet, on_delete=models.SET_NULL, default=None, null=True)
    target_ips = models.CharField(max_length=2048)
    AttackIntensity = enum(
        LOW='low',
        MIDDLE='middle',
        HIGH='high',
    )
    attack_intensity = models.CharField(max_length=20, default=AttackIntensity.LOW)

    name = models.CharField(max_length=100)
    type = models.PositiveIntegerField(default=EnvAttacker.Type.OBFUSCATION_FLOW)
    desc = models.TextField(default='')
    file = models.FileField(upload_to='envattacker', null=True, default=None)
    json_config = models.TextField(default='{}')

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    team = models.ForeignKey(Team, null=True, default=None, on_delete=models.SET_NULL)

    Status = enum(
        DELETED=0,
        CREATING=1,
        USING=2,
        ERROR=3,
        PAUSE=4,
    )
    status = models.IntegerField(default=Status.CREATING)
    # 记录出错信息
    error = models.CharField(max_length=2048, default=None, null=True)

    # 环境创建时间
    create_time = models.DateTimeField(default=timezone.now)
    # 环境创建完成时间
    created_time = models.DateTimeField(default=None, null=True)
    # 环境创建消耗时间
    consume_time = models.PositiveIntegerField(default=0)
    # 修改时间
    modify_time = models.DateTimeField(default=timezone.now)

    servers = models.ManyToManyField(EnvTerminal)


class ServerCreatePool(models.Model):
    unique_id = models.CharField(max_length=100, unique=True)
    create_time = models.DateTimeField(default=timezone.now)
    estimate_consume_time = models.PositiveIntegerField(default=0)


class WaitingCreatePool(ExecutePool):
    consume_count = models.PositiveIntegerField(default=1)
    estimate_consume_time = models.PositiveIntegerField(default=0)


__all__ = ['Env', 'EnvNet', 'EnvGateway', 'EnvTerminal', 'EnvAttacker', 'EnvAttackerInstance',
           'SnapshotEnvMap', 'TestEnvMap', 'StandardDeviceEditServer', 'StandardDevice', 'ServerCreatePool',
           'WaitingCreatePool']
