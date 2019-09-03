# -*- coding: utf-8 -*-
import commands
import json
import socket
import paramiko
import time
import logging
import re
import os
import ConfigParser

import pymysql
import requests
from django.conf import settings
from django.contrib.auth.models import Group

from common_auth.models import User
from common_auth.constant import GroupType
from system_configuration.models import SystemConfiguration

logging.getLogger('paramiko').setLevel(logging.WARNING)


SUCCESS = 'OK'
FAILED = 'failed'


def get_host_ip():
    """
    查询本机ip地址
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


class SSHClient(object):

    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, hostname, username, password, port=22):
        try:
            self.ssh.connect(hostname=hostname, port=port, username=username, password=password, timeout=10)
            time.sleep(2)
        except:
            self.ssh.close()
            return FAILED
        self.ssh.close()
        return SUCCESS


class OJ(object):
    oj_doc = 'OJ 服务: '
    oj_space = '    '
    oj_error = '==>'
    error_count = 0
    BOOT = ("supervisord", "mariadb", "memcached")
    error_msgs = []

    def debug(self):
        flag = settings.DEBUG and FAILED or SUCCESS
        self.error(flag, 'DEBUG 开启')
        return flag

    def ip(self):
        PROXY_IP = settings.XCTF_CONFIG['common_proxy']['PROXY_IP']
        if get_host_ip() == settings.SERVER_IP == settings.SERVER_INTERNET_IP == PROXY_IP:
            return SUCCESS
        self.error(FAILED, "配置SERVER_IP 或者 SERVER_INTERNET_IP 或者 PROXY_IP 和本地ip不一致")
        return FAILED

    def node(self):
        node_path = settings.XCTF_CONFIG["COURSE"]["NODE_PATH"]
        cmd = 'ls -l {}'.format(node_path)
        status, output = commands.getstatusoutput(cmd)
        if status == 0:
            return SUCCESS
        self.error(FAILED, 'node 未安装, 或者未配置正确的node路径')
        return FAILED

    def common_cloud(self):
        # todo 需要检测端口, 80还是8000 什么的
        CLOUD_CENTER = settings.XCTF_CONFIG["COMMON_CLOUD"]["CLOUD_CENTER"]

        search_group = re.search('^127\.0\.0\.1(:80)?$', CLOUD_CENTER)
        if search_group: return SUCCESS

        self.error(FAILED, '云端交流 CLOUD_CENTER 配置不匹配 --> 127.0.0.1 or 127.0.0.1:80')
        return FAILED

    def enable_boot(self):
        """
        验证开机启动 systemctl is-enabled mysql
        """
        boot_success = {}
        for boot in self.BOOT:
            status, output = self._commands('systemctl is-enabled {}'.format(boot))
            if status != 0:
                self.error(FAILED, '{} 没有开机启动'.format(boot))
                boot_success[boot] = FAILED
            else:
                boot_success[boot] = SUCCESS
        return '\n' + json.dumps(boot_success, sort_keys=True, indent=4)

    def x_vulns_server(self):
        """
        漏洞库
        """
        try:
            r = requests.get(settings.XCTF_CONFIG['x_vulns']['SERVER'], timeout=5)
            status_code = r.status_code
            if status_code == 200:
                return SUCCESS
            else:
                return FAILED
        except:
            self.error(FAILED, '漏洞库镜像链接访问失败')
            return FAILED

    def init_oj_data(self):
        init_data = {
            'Group': SUCCESS,
            'AdminUser': SUCCESS,
            'AdminAddGroup': SUCCESS,
            'SystemConfiguration': SUCCESS,
        }
        group_count = Group.objects.count()
        if group_count == 0:
            self.error(FAILED, 'init_data 用户组数据未进行初始化')
            init_data['Group'] = FAILED

        admin_user = User.objects.filter(username='admin').exclude(status=0).first()
        if not admin_user:
            self.error(FAILED, 'init_data 未初始化admin数据')
            init_data['AdminUser'] = FAILED
        else:
            # 用户未添加角色自动添加角色
            if not admin_user.groups.exists():
                admin_user.groups.add(GroupType.ADMIN)
            #     self.error(FAILED, 'admin用户未添加组分类')
            #     init_data['AdminAddGroup'] = FAILED

        sys_count = SystemConfiguration.objects.count()
        if sys_count < 2:
            self.error(FAILED, 'init_data 未添加系统配置数据SystemConfiguration')
            init_data['SystemConfiguration'] = FAILED

        return '\n' + json.dumps(init_data, sort_keys=True, indent=4)

    def vis(self):
        """
        态势
        """
        vis_host = settings.VIS_HOST
        check_vis_host = settings.CHECK_VIS_HOST
        if vis_host.startswith('127.0.0.1') or check_vis_host.startswith('127.0.0.1'):
            self.error(FAILED, 'VIS_HOST or CHECK_VIS_HOST未修改地址')
            return FAILED

        for request_host in (vis_host, check_vis_host):
            status, output = self._commands('curl {} -L'.format(request_host))
            if '</html>' not in output:
                self.error(FAILED, msg='vis_host, check_vis_host {} 访问失败'.format(request_host))
                return FAILED

        return SUCCESS

    def openstack(self):
        scene = settings.XCTF_CONFIG['scene']
        os_auth = scene['OS_AUTH']
        complex_misc = scene['COMPLEX_MISC']

        username = os_auth['username']
        password = os_auth['password']
        project_name = os_auth['project_name']
        project_id = os_auth['project_id']

        external_net = complex_misc['external_net']

        openstack_data = {
            "OS_AUTH.username": SUCCESS,
            "OS_AUTH.password": SUCCESS,
            "OS_AUTH.project_name": SUCCESS,
            "OS_AUTH.project_id": SUCCESS,
            "COMPLEX_MISC.external_net": SUCCESS,
        }

        # self._commands("source ~/admin.openrc")

        status, output = self._commands("cat ~/admin.openrc |grep -E '^export OS_USERNAME={}$'".format(username))
        if status != 0:
            self.error(FAILED, 'openstack username 不正确')
            openstack_data['OS_AUTH.username'] = FAILED
        status, output = self._commands("cat ~/admin.openrc |grep -E '^export OS_PASSWORD={}$'".format(password))
        if status != 0:
            self.error(FAILED, 'openstack password 不正确')
            openstack_data['OS_AUTH.password'] = FAILED
        status, output = self._commands(
            "cat ~/admin.openrc |grep -E '^export OS_PROJECT_NAME={}$'".format(project_name))
        if status != 0:
            self.error(FAILED, 'openstack project_name 不正确')
            openstack_data['OS_AUTH.project_name'] = FAILED
        status, output = self._commands("source ~/admin.openrc && openstack project list | grep {}".format(project_id))
        if status != 0:
            self.error(FAILED, 'openstack project_id 不正确 --> {}'.format(project_id))
            openstack_data['OS_AUTH.project_id'] = FAILED

        status, output = self._commands("source ~/admin.openrc && openstack network list --external| grep {}".format(external_net))
        if status != 0:
            self.error(FAILED, 'openstack external_net 不正确  --> {}'.format(external_net))
            openstack_data['COMPLEX_MISC.external_net'] = FAILED

        return '\n' + json.dumps(openstack_data, sort_keys=True, indent=4)

    def oj_database(self):
        default = settings.DATABASES["default"]
        host = default['HOST']
        if get_host_ip() != host:
            self.error(FAILED, 'OJ 数据库host 配置出错')
            return FAILED
        flag = self._database(default)
        self.error(flag, 'OJ 数据库配置出错')
        return self._flag(flag)

    def guacamole(self):
        guacamole_data = {
            'DATABASE': SUCCESS,
            "OJ_SERVER": SUCCESS,
            "GUACAMOLE_SERVERS": SUCCESS,
        }
        common_remote = settings.XCTF_CONFIG['common_remote']
        flag_db = self._guacamole_database(common_remote['DATABASE'])
        flag_oj = self._guacamole_oj_server(common_remote['OJ_SERVER'])
        flag_server = self._guacamole_guacamole_servers(common_remote['GUACAMOLE_SERVERS'])
        if flag_db == FAILED:
            guacamole_data['DATABASE'] = FAILED
        if flag_oj == FAILED:
            guacamole_data['OJ_SERVER'] = FAILED
        if flag_server == FAILED:
            guacamole_data['GUACAMOLE_SERVERS'] = FAILED
        return '\n' + json.dumps(guacamole_data, sort_keys=True, indent=4)

    def nova_config(self):
        conf_file = "/etc/nova/nova.conf"
        if not os.path.isfile(conf_file):
            self.error(FAILED, 'nova.conf file is not exists')
            return FAILED

        cp = ConfigParser.ConfigParser()
        cp.read(conf_file)
        enabled_vnc = enabled_spice = False
        try:
            enabled_vnc = cp.get(section='vnc', option='enabled')
        except:
            pass
        try:
            enabled_spice = cp.get(section='spice', option='enabled')
        except:
            pass
        if enabled_vnc == 'true' or enabled_spice == 'true':
            return SUCCESS
        self.error(FAILED, 'vnc or spice is not set enabled=true')
        return FAILED

    def error(self, flag, msg='error'):
        if flag == SUCCESS or flag == 0:
            pass
        else:
            self.error_count += 1
            self.error_msgs.append(self.oj_error + "错误原因: " + msg)

    def _guacamole_database(self, database):
        host = database['HOST']
        if get_host_ip() != host:
            self.error(FAILED, 'guacamole 数据库host 配置出错')
            return FAILED
        flag = self._database(database)
        self.error(flag, msg='common_remote database can not connect')
        return self._flag(flag)

    def _guacamole_oj_server(self, oj_server):
        host_ip = oj_server['host_ip']
        ssh_username = oj_server['ssh_username']
        ssh_password = oj_server['ssh_password']
        flag = SSHClient().connect(hostname=host_ip, username=ssh_username, password=ssh_password)
        self.error(flag, 'common_remote OJ_SERVER ssh 链接不上')
        return self._flag(flag)

    def _guacamole_guacamole_servers(self, guacamole_servers):
        return_flag = True
        for guacamole_server in guacamole_servers:
            host_ip = guacamole_server['host_ip']
            host_ip = "".join([host_ip, ':'])
            server = guacamole_server['server']
            if host_ip not in server:
                return_flag = False
                self.error(FAILED, msg='GUACAMOLE_SERVERS host_ip not in the server, please checker')

            public_server = guacamole_server['public_server']
            if public_server != server:
                return_flag = False
                self.error(FAILED, msg='GUACAMOLE_SERVERS public_server not the same server, please checker')
            ssh_username = guacamole_server['ssh_username']
            ssh_password = guacamole_server['ssh_password']
            status, output = self._commands('curl --connect-timeout 10 {}/guacamole/'.format(server))
            if '</html>' not in output:
                return_flag = False
                self.error(FAILED, msg='GUACAMOLE_SERVERS server {}/guacamole/ 访问失败'.format(server))

        return return_flag and SUCCESS or FAILED

    def _database(self, database):
        name = database['NAME']
        user = database['USER']
        password = database['PASSWORD']
        host = database['HOST']
        port = database['PORT']
        try:
            db = pymysql.connect(host, user, password, name, port=int(port))
            db.close()
        except:
            return FAILED
        return SUCCESS

    def _commands(self, shell):
        status, output = commands.getstatusoutput(shell)
        return status, output

    def _flag(self, flag):
        if flag == 0 or flag == SUCCESS:
            return SUCCESS
        return FAILED

    def _request(self, url, timeout=5):
        try:
            r = requests.get(url, timeout=timeout)
            status_code = r.status_code
            if status_code == 200:
                return SUCCESS
            else:
                return FAILED
        except:
            return FAILED

    def not_checker_in_oj(self):
        if settings.PLATFORM_TYPE != 'OJ':
            print self.oj_space + ": ".join(['攻防,态势', self.vis()])

    def checker(self):
        print self.oj_doc
        print self.oj_space + ": ".join(['DEBUG', self.debug()])
        print self.oj_space + ": ".join(['SERVER_IP', self.ip()])
        print self.oj_space + ": ".join(['node配置', self.node()])
        print self.oj_space + ": ".join(['云端交流', self.common_cloud()])
        print self.oj_space + ": ".join(['guacamole', self.guacamole()])
        print self.oj_space + ": ".join(['开机自启服务', self.enable_boot()])
        print self.oj_space + ": ".join(['攻防,漏洞库检测', self.x_vulns_server()])
        # print self.oj_space + ": ".join(['攻防,态势', self.vis()])
        print self.oj_space + ": ".join(['初始化数据检测', self.init_oj_data()])
        print self.oj_space + ": ".join(['OJ Openstack配置检查', self.openstack()])
        print self.oj_space + ": ".join(['OJ 数据库检查', self.oj_database()])
        print self.oj_space + ": ".join(['nova.conf', self.nova_config()])
        self.not_checker_in_oj()
        print '--------------error count: ' + str(self.error_count) + '--------------'
        print "详细信息: "
        for error in self.error_msgs:
            print error
        print
        return ''
