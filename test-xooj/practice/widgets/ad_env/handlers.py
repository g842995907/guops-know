# -*- coding: utf-8 -*-
import copy
import json
import logging
import os
import uuid

from django.conf import settings
from retry import retry

from common_env.handlers import manager as common_manager
from common_env.handlers.common import parse_system_users
from common_env.handlers.exceptions import MsgException
from common_env.handlers.local_lib import scene
from common_env.models import Env, EnvTerminal
from common_env.rpc.client import checker
from event_attack_defense.setting import api_settings as ad_api_settings
from event_attack_defense.util.ssh import ssh
from .error import error

logger = logging.getLogger(__name__)

ssh_port = ad_api_settings.SSH_PORT
ssh_user = ad_api_settings.SSH_USER
ssh_rsa_key_path = ad_api_settings.SSH_RSA_KEY_PATH


class BaseExecuter(common_manager.BaseExecuter):
    def _add_ssh_connection(self, hostname, port=22, username=None, password=None, private_key=None):
        if self.backend_admin:
            with open(ssh_rsa_key_path, 'r') as rsa_key_file:
                rsa_key_content = rsa_key_file.read()
                return super(BaseExecuter, self)._add_ssh_connection(hostname, ssh_port, ssh_user,
                                                                     private_key=rsa_key_content)
        else:
            return super(BaseExecuter, self)._add_ssh_connection(hostname, port, username, private_key=private_key)


class Creater(BaseExecuter, common_manager.Creater):
    # 攻防模式默认添加ssh
    def _create_envterminals(self, env):
        super(Creater, self)._create_envterminals(env)
        envterminals = env.envterminal_set.all()
        for envterminal in envterminals:
            access_modes = json.loads(envterminal.access_modes)
            protocols = [mode['protocol'] for mode in access_modes]
            if EnvTerminal.AccessMode.SSH not in protocols:
                system_users = self.get_system_users(access_modes)
                for user in system_users:
                    access_modes.append({
                        'protocol': EnvTerminal.AccessMode.SSH,
                        'port': EnvTerminal.AccessModeDefaultPort[EnvTerminal.AccessMode.SSH],
                        'username': user['username'],
                        'password': user['password'],
                    })
                envterminal.access_modes = json.dumps(access_modes)
            envterminal.save()


class Getter(BaseExecuter, common_manager.Getter):
    pass


class Deleter(BaseExecuter, common_manager.Deleter):
    pass


# 环境处理, 创建销毁环境
class EnvHandler(object):

    def __init__(self, user, **kwargs):
        self.user = user
        self.team = kwargs.get('team', None)
        self.create_params = kwargs.pop('create_params', None)

        kwargs.update({
            'remote': kwargs.get('remote', False),
            'getter_class': kwargs.get('getter_class', Getter),
            'creater_class': kwargs.get('creater_class', Creater),
            'deleter_class': kwargs.get('deleter_class', Deleter),
        })
        self.base_handler = common_manager.EnvHandler(user, **kwargs)

        if self.team:
            self.group_filter_params = {
                'env__team': self.team
            }
        else:
            self.group_filter_params = {
                'env__user': self.user
            }

    def get_name_prefix(self, task, template_task_env):
        return '{type}.{player}.{task}'.format(
            type='AD',
            player=self.team.name if self.team else self.user.username,
            task=task.title,
        )

    def get_template_task_env(self, task):
        template_task_env = task.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not template_task_env:
            raise MsgException(error.TASK_ENV_NOT_CONFIGURED)
        return template_task_env

    def check_create(self, task):
        using_status = Env.ActiveStatusList

        # 当前题目使用的环境
        using_task_envs = task.envs.filter(env__status__in=using_status)

        # 检查是否已创建环境
        if using_task_envs.filter(**self.group_filter_params).exists():
            raise MsgException(error.TASK_ENV_EXIST)

        # 检查环境数量是否已满
        using_envs = Env.objects.filter(status__in=using_status)
        if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
            raise MsgException(error.FULL_ENV_CAPACITY)

    def create(self, task):
        self.check_create(task)
        template_task_env = self.get_template_task_env(task)

        task_env = copy.copy(template_task_env)
        task_env.pk = None

        name_prefix = self.get_name_prefix(task, template_task_env)
        # 攻防部署模式
        if self.create_params:
            terminals = []
            network_id = self.create_params['network_id']
            for sub_id, fixed_ip in self.create_params['server_ip'].items():
                terminals.append({
                    'network_id': network_id,
                    'sub_id': sub_id,
                    'fixed_ip': fixed_ip,
                    'allocate_float_ip': True,
                })
            # 如果存在checker移除checker
            for envterminal in task_env.env.envterminal_set.filter(role=EnvTerminal.Role.EXECUTER):
                terminals.append({
                    'sub_id': envterminal.sub_id,
                    'remove': True,
                })
            hang_info = {'terminals': terminals}
        else:
            hang_info = None

        task_env.env = self.base_handler.create(task_env.env, name_prefix=name_prefix, hang_info=hang_info)

        # is_copy指的是比赛中的场景
        if task.is_copy:
            task_env.destroy_delay = 0

        task_env.save()
        task.envs.add(task_env)

        return task_env

    # 攻防部署时调用
    def create_checker(self, task):
        template_task_env = self.get_template_task_env(task)
        template_env = template_task_env.env
        checker_terminal = template_env.envterminal_set.filter(role=EnvTerminal.Role.EXECUTER).first()
        if not checker_terminal:
            return None

        json_config = json.loads(template_env.json_config)
        servers = [server for server in json_config['servers'] if server['id'] == checker_terminal.sub_id]
        if not servers:
            return None

        checker_json_config = {
            'scene': {
                'name': '%s-checker' % json_config['scene'].get('name'),
            },
            'servers': servers
        }
        config = {
            'json_config': json.dumps(checker_json_config),
            'file': template_env.file,
            'type': Env.Type.BASE,
        }
        name_prefix = '{type}.{task}.checker'.format(
            type='AD',
            task=task.title,
        )
        return self.base_handler.create(name_prefix=name_prefix, config=config, hang_info={'keep': 1})

    def delete(self, task, async=True):
        task_envs = task.envs.filter(
            env__status__in=Env.UseStatusList,
            **self.group_filter_params
        )

        for task_env in task_envs:
            # 私有环境直接删掉
            self.base_handler.delete(task_env.env, async)

    def get(self, task, is_complete=False):
        try:
            task_env = self.get_task_env(task)
        except MsgException as e:
            task_env = self.get_template_task_env(task)
        data = self.base_handler.get(task_env.env, is_complete)
        return data

    def get_task_env(self, task, raise_exception=True):
        using_task_envs = task.envs.filter(env__status__in=Env.ActiveStatusList)
        task_env = using_task_envs.filter(**self.group_filter_params).first()
        if raise_exception and not task_env:
            raise MsgException(error.TASK_ENV_NOT_EXIST)
        return task_env

    def execute_script(self, task, envterminal_sub_id, mode):
        if not self.base_handler.is_admin:
            raise MsgException(error.NO_PERMISSION)

        mode_exec = {
            2: self._init_task,
            3: self._clean_task,
            4: self._push_flag,
            5: self._check_task,
        }

        if mode not in mode_exec:
            raise MsgException(error.NO_PERMISSION)

        task_env = self.get_task_env(task)
        envterminal = task_env.env.envterminal_set.filter(sub_id=envterminal_sub_id).first()
        if not envterminal:
            raise MsgException(error.ENVTERMINAL_NOT_EXIST)
        return mode_exec[mode](task, envterminal)

    def _upload_all_file(self, task, envterminal, client):
        task_local_path = self._get_task_local_path(task)
        task_remote_path = self._get_task_remote_path(task)
        self._run_script(client, 'rm -rf %s' % task_remote_path)

        client.upload_dir(task_local_path, task_remote_path)

        deploy_script = os.path.join(task_remote_path, envterminal.deploy_script)
        clean_script = os.path.join(task_remote_path, envterminal.clean_script)
        push_flag_script = os.path.join(task_remote_path, envterminal.push_flag_script)

        self._run_script(client, "chmod %d %s" % (700, deploy_script))
        self._run_script(client, "chmod %d %s" % (700, clean_script))
        self._run_script(client, "chmod %d %s" % (700, push_flag_script))

    def _depoly(self, task, envterminal, client):
        deploy_script = envterminal.deploy_script
        clean_script = envterminal.clean_script
        task_remote_path = self._get_task_remote_path(task)

        cmd_clean = 'cd %s && ./%s' % (task_remote_path, clean_script)
        task_port = self.get_env_service_port(envterminal)
        cmd_deploy = 'cd %s && ./%s %s:%d' % (task_remote_path, deploy_script, envterminal.float_ip, task_port)

        self._run_script(client, cmd_clean)
        self._run_script(client, cmd_deploy)

    def _get_task_local_path(self, task):
        template_task_env = self.get_template_task_env(task)
        return os.path.join(settings.BASE_DIR, "common_env", "media", "env_files", str(template_task_env.env.id))

    def _get_task_remote_path(self, task):
        return os.path.join(ad_api_settings.TASK_DEPLOY_PATH, task.title)

    def _init_task(self, task, envterminal):
        host = envterminal.float_ip
        client = None
        try:
            # 初始化checker docker
            self._init_checker_docker(task, envterminal)

            client = ssh(host, ssh_port, ssh_user, key_path=ssh_rsa_key_path)
            self._upload_all_file(task, envterminal, client)
            self._depoly(task, envterminal, client)
        except Exception as e:
            if client:
                client.close()
            raise e

        return True

    def _init_checker_docker(self, task, envterminal):
        task_env = self.get_task_env(task)
        docker_envterminal = task_env.env.envterminal_set.filter(sub_id=envterminal.checker).first()
        container_id = docker_envterminal.vm_id
        if not container_id: return None

        try:
            # 修改checker机器密码
            password = self._get_docker_password(docker_envterminal)
            scene.docker.execute_command(container_id,
                                         "/bin/bash -c \"echo 'root:{password}' | chpasswd\"".format(password=password))

            # 重启ssh
            scene.docker.execute_command(container_id, 'service ssh start')

            # 启动supervisor
            scene.docker.execute_command(container_id, 'supervisord -c /etc/supervisor/supervisord.conf')
        except Exception as e:
            logger.info("done after checker error, msg[%s]", str(e))
            raise e

    def _clean_task(self, task, envterminal):
        host = envterminal.float_ip
        client = ssh(host, ssh_port, ssh_user, key_path=ssh_rsa_key_path)
        clean_script = envterminal.clean_script
        task_remote_path = self._get_task_remote_path(task)
        cmd_clean = 'cd %s && ./%s' % (task_remote_path, clean_script)

        self._run_script(client, cmd_clean)
        return True

    def _push_flag(self, task, envterminal):
        host = envterminal.float_ip
        client = ssh(host, ssh_port, ssh_user, key_path=ssh_rsa_key_path)
        task_remote_path = self._get_task_remote_path(task)
        push_flag_script = os.path.join(task_remote_path, envterminal.push_flag_script)

        self._run_script(client, "%s %s" % (push_flag_script, 'this_is_flag_' + str(uuid.uuid4())))

        return True

    def _check_task(self, task, envterminal):
        # checker_path = self._get_checker_script_path(task, envterminal)
        # if checker_path is None or not os.path.exists(checker_path):
        #     raise MsgException(error.CHECK_SCRIPT_PATH_NULL)
        #
        # try:
        #     script_module = imp.load_source('xctf_checker_script', checker_path)
        #     result = script_module.checker(envterminal.float_ip, self.get_env_service_port(envterminal))
        # except Exception, e:
        #     raise e
        # return result
        task_env = self.get_task_env(task)
        docker_envterminal = task_env.env.envterminal_set.filter(sub_id=envterminal.checker).first()
        if not envterminal:
            raise MsgException(error.ENVTERMINAL_NOT_EXIST)

        try:
            # 上传checker文件到checker机器上
            self._upload_checker_file(task, envterminal, docker_envterminal)

            # rpc调用checker
            result = checker(docker_envterminal.float_ip, "/home/checker.py", envterminal.float_ip,
                             self.get_env_service_port(envterminal))

        except Exception as e:
            logger.info("check error msg[%s]", str(e))
            return None

        return result

    def _get_docker_password(self, envterminal):
        if hasattr(self, '_docker_password'):
            return self._docker_password

        password = None
        users = parse_system_users(json.loads(envterminal.access_modes))
        if not users:
            logger.warning("there is no any user in access_modes")
        else:
            for user in users:
                if user.get('username') == 'root':
                    password = user.get('password')
                    break

        if not password:
            password = "fsH7yBxo8pwWxn8nPBT7"

        self._docker_password = password
        return password

    @retry(tries=3, delay=1)
    def _upload_checker_file(self, task, envterminal, docker_envterminal):

        try:
            with self._get_docker_ssh_client(docker_envterminal) as ssh_client:
                checker_path = self._get_checker_script_path(task, envterminal)

                if os.path.exists(checker_path):
                    ssh_client.upload(checker_path, "/home/checker.py")
        except Exception as e:
            logger.info("upload checker file error, msg[%s]", str(e))
            raise e

    @retry(tries=3, delay=1)
    def _get_docker_ssh_client(self, envterminal):
        try:
            password = self._get_docker_password(envterminal)
            client = ssh(envterminal.float_ip, 22, 'root', password=password)
            return client
        except Exception as e:
            logger.info("get_ssh_client error msg[%s]", str(e))
            raise e

    def _run_script(self, client, cmd):
        cmd = cmd.encode('utf-8')

        stdin, stdout, stderr = client.exe(cmd)
        err = stderr.readlines()
        if err:
            raise MsgException("%s %s" % (error.RUN_SCRIPT_ERROR, err))

    def get_env_service_port(self, env_server):
        filter_name_list = (
            EnvTerminal.AccessMode.SSH,
            EnvTerminal.AccessMode.CONSOLE,
            EnvTerminal.AccessMode.RDP,
            EnvTerminal.AccessMode.TELNET,
        )

        access_modes = json.loads(env_server.access_modes)
        for access_mode in access_modes:
            protocol = access_mode['protocol']
            port = access_mode.get('port', 0)

            if port != 0 and protocol not in filter_name_list:
                return port
        return 0

    def _get_checker_script_path(self, task, envterminal):
        template_task_env = self.get_template_task_env(task)
        path = os.path.join(settings.BASE_DIR, "common_env", "media", "env_files", str(template_task_env.env.id))
        try:
            if envterminal.checker:
                checker_terminal = envterminal.env.envterminal_set.filter(sub_id=envterminal.checker).first()
                if checker_terminal:
                    checker_file = checker_terminal.check_script
                    if checker_file and checker_file.strip() != '':
                        path = os.path.join(path, checker_file)
                        return path
                    else:
                        return None
        except Exception, e:
            return None

        return None
