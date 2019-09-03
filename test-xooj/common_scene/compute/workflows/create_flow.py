from __future__ import unicode_literals

import functools
import logging
import memcache
import os
import random
from retry import retry
import threading
import time
import urlparse

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneCreator, logger_decorator, check_kwargs
from common_scene import params
from common_scene.setting import api_settings
from common_scene import utils as project_utils


LOG = logging.getLogger(__name__)
ATTEMPTS = 60
WINDOWS = "windows"
LINUX = "linux"
FAULT_MAP = {
    'NoValidHost': _("There is not enough capacity for this "
                     "flavor in the selected availability zone. "
                     "Please try again later.")
}


class ServerSceneCreator(BaseSceneCreator):
    def __init__(self, request_id, **kwargs):
        super(ServerSceneCreator, self).__init__(request_id, **kwargs)

    def _generate_inst_user_data(self, vm_id, image_type, users, attach_url,
                            install_script=None, init_script=None, from_snapshot=False):
        if image_type.lower() == WINDOWS:
            self.temp_users[vm_id] = []
            userdata = params.powershell_start

            # status change to started
            userdata += params.windows_send_message2oj.format(
                                env_id=self.request_id, vm_id=vm_id, status=4,
                                report_url=api_settings.COMPLEX_MISC.get("report_vm_status"))

            # add user for windows instance
            if users:
                # has_xctf_user = False
                for user in users:
                    username = user.get("username")
                    password = user.get("password") or project_utils.generate_complex_str()
                    self.temp_users[vm_id].append({'username': username, 'password': password})
                    userdata += params.windows_user_create.format(username=username)
                    userdata += params.windows_change_user_pwd.format(username=username,
                                                                      password=password)
                    userdata += params.windows_add_user_to_rdp.format(username=username)

                    # if username == "xctf":
                    #     has_xctf_user = True
            else:
                # if not has_xctf_user:
                # change xctf user password
                xctf_pwd = project_utils.generate_complex_str()
                userdata += params.windows_change_user_pwd.format(username="xctf", password=xctf_pwd)
                self.temp_users[vm_id].append({'username': "xctf", 'password': xctf_pwd})

            if attach_url:
                # download zip file
                zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
                file_folder = os.path.splitext(zip_file_name)[0]
                userdata += params.windows_download_zip.format(zip_file_name=zip_file_name,
                                                       attach_url=attach_url,
                                                       file_folder=file_folder)

                if install_script:
                    # execute install scripts
                    script_path = install_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += params.windows_install_evn.format(file_folder=file_folder,
                                                          script_folder=script_folder,
                                                          install_script=install_script)
                if init_script:
                    script_path = init_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += params.windows_init_services.format(file_folder=file_folder,
                                                            script_folder=script_folder,
                                                            init_script=init_script)

                # delete zip file if not debug
                if api_settings.COMPLEX_MISC.get("clean_env", False):
                    userdata += params.windows_clean_env.format(file_folder=file_folder)

            # status change to running
            userdata += params.windows_send_message2oj.format(
                                env_id=self.request_id, vm_id=vm_id, status=6,
                                report_url=api_settings.COMPLEX_MISC.get("report_vm_status"))
            return userdata
        elif image_type.lower() == LINUX:
            self.temp_users[vm_id] = []
            userdata = params.user_data_start
            root_pwd = ""

            # pop root user
            for idx, user in enumerate(users):
                if user.get("username") == "root":
                    root_pwd = users.pop(idx).get("password", "").strip()
                    break

            root_pwd = root_pwd or project_utils.generate_complex_str(length=12)
            userdata += params.change_root_pwd.format(root_pwd=root_pwd)
            self.temp_users[vm_id].append({'username': "root", 'password': root_pwd})

            # create users
            if users:
                groups = []
                userdata += params.add_group_prefix
                userdata += params.add_user_prefix
                for user in users:
                    username = user.get("username")
                    password = user.get("password") or project_utils.generate_complex_str(length=12)
                    sudo = user.get("permission",{}).get("sudo")
                    if username == "root":
                        continue
                    groups.append(params.add_group.format(group=username))
                    self.temp_users[vm_id].append({'username': username,
                                                   'password': password})
                    if sudo:
                        userdata += params.add_user_with_sudo.format(
                                                           group=username,
                                                           username=username,
                                                           password=password)
                    else:
                        userdata += params.add_user.format(group=username,
                                                           username=username,
                                                           password=password)
                # add groups
                userdata = userdata.format(groups="".join(groups))
            # else:
            #     xctf_pwd = project_utils.get_random_string(length=12)
            #     userdata += params.add_xctf_user.format(xctf_pwd=xctf_pwd)
            #     self.temp_users[vm_id].append({'username': "xctf", 'password': xctf_pwd})

            # custom shell script start
            userdata += params.script_block_start

            # status change to started
            userdata += params.send_message2oj_new.format(
                                env_id=self.request_id, vm_id=vm_id, status=4,
                                report_url=api_settings.COMPLEX_MISC.get("report_vm_status"))

            if attach_url:
                # download zip file
                zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
                file_folder = os.path.splitext(zip_file_name)[0]
                userdata += params.download_zip.format(zip_file_name=zip_file_name,
                                                       attach_url=attach_url,
                                                       file_folder=file_folder)
                if install_script and not from_snapshot:
                    # execute install scripts
                    script_path = install_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += params.install_evn.format(file_folder=file_folder,
                                                          script_folder=script_folder,
                                                          install_script=install_script)
                if init_script:
                    script_path = init_script.split()[0]
                    script_folder = os.path.join(file_folder, os.path.split(script_path)[0])
                    userdata += params.init_services.format(file_folder=file_folder,
                                                            script_folder=script_folder,
                                                            init_script=init_script)

                # delete zip file if not debug
                if api_settings.COMPLEX_MISC.get("clean_env", False):
                    userdata += params.clean_env.format(file_folder=file_folder)

            # status change to running
            userdata += params.send_message2oj_new.format(
                                env_id=self.request_id, vm_id=vm_id, status=6,
                                report_url=api_settings.COMPLEX_MISC.get("report_vm_status"))

            # user data end line
            userdata += params.user_data_end
            return userdata
        return None

    def _instance_fault_to_friendly_message(self, fault):
        message = fault.get('message', _("Unknown"))
        default_message = _("Please try again later [Error: %s].") % message
        return FAULT_MAP.get(message, default_message)

    def _analysis_init_script(self, init_script):
        try:
            result = []
            params = init_script.split()
            for param in params:
                if param.startswith("{FLAG"):
                    result.append(param.format(FLAG=self.flags))
                elif param.endswith(".ip}"):
                    result.append(self.pre_allocation_ips.get(param[1:-1]))
                else:
                    result.append(param)
            return " ".join(result)
        except Exception, e:
            err_msg = _('Unable to analysis init script. "{}"').format(init_script)
            self._handle_error(err_msg, e)

    def _create_server(self, **kwargs):
        vm_id = kwargs.pop("vm_id")
        try:
            inst = self.nova_cli.instance_create(**kwargs)
            LOG.info("Created instance {} .".format(kwargs.get("name")))
            self.resources['servers'].update({vm_id: inst})
            return inst
        except Exception, e:
            err_msg = _("Unable to create instance {}.").format(vm_id)
            self._handle_error(err_msg, e)

    def _check_vm_status(self, inst):
        inst_id = inst.id if hasattr(inst, "id") else inst

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check status for instance {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(inst_id)
                break
            server = self.nova_cli.instance_get(inst_id)
            if server.status == "ACTIVE":
                msg = "Instance {} status Active.".format(inst_id)
                LOG.info(msg)
                return server
            elif server.status == "ERROR":
                err_msg = self._instance_fault_to_friendly_message(getattr(server, 'fault', {}))
                break
            LOG.debug("Instance status not active. "
                      "Try again 1 second later...")
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    def inst_add_qos_policy(self, inst_key, net_key, instance, qos_rules=None):
        if not qos_rules:
            err_msg = _("No qos rules found for "
                        "instance {}").format(instance.name)
            LOG.debug(err_msg)
            return False

        policy_name = "{}-{}-qos".format(inst_key, net_key)
        try:
            policy = self.neutron_cli.qos_policy_create(name=policy_name)
            for rule_dict in qos_rules:
                self.neutron_cli.qos_bandwidth_limit_rule_create(
                    policy.get("id"), **rule_dict)
            self.resources["qoses"].update({inst_key: policy})
        except Exception, e:
            err_msg = _("Unable to create qos policy {}").format(policy_name)
            self._handle_error(err_msg, e)

        try:
            ports = self._get_ports(instance, self.resources["networks"].get(net_key))
            for port in ports:
                self.bind_port_qos_policy(port.get("id"), policy.get("id"))
            return True
        except Exception, e:
            err_msg = _("Unable to bind qos policy {} "
                        "to instance {}").format(policy_name, instance.name)
            self._handle_error(err_msg, e)

    @logger_decorator
    @check_kwargs("id", "image")
    def create_server(self, **kwargs):
        vm_id = kwargs.get("id")
        name = kwargs.get("name")

        from_snapshot, image = self._get_image(kwargs.get("image"))

        image_type = kwargs.get("imageType", "linux").lower()
        flavor = self._get_flavor(image_type, kwargs.get("flavor"))

        vm_nets = kwargs.get("net") or ['openstack']
        nics = self._analysis_networks(vm_id, vm_nets,
                                       kwargs.get("global_network"),
                                       kwargs.get("fixed_ip"))

        install_script = kwargs.get("installScript")
        init_script = kwargs.get("initScript")
        if init_script:
            init_script = self._analysis_init_script(init_script)
        user_data = self._generate_inst_user_data(vm_id=vm_id,
                                             image_type=image_type,
                                             users=kwargs.get("accessUser", []),
                                             attach_url=self.attach_url,
                                             install_script=install_script,
                                             init_script=init_script,
                                             from_snapshot=from_snapshot)
        LOG.debug(user_data)
        avail_zone = kwargs.get("availability_zone", None)
        security_groups = api_settings.COMPLEX_MISC.get("security_groups", ['default'])

        inst = self._create_server(vm_id=vm_id, name=name, image=image,
                                   flavor=flavor, nics=nics,
                                   security_groups=security_groups,
                                   key_name=None,
                                   user_data=user_data,
                                   availability_zone=avail_zone)
        inst = self._check_vm_status(inst)

        # Associate floating ip
        vm_role = kwargs.get("role")
        if self._need_floating_ip(vm_role):
            fip_obj = self.bind_floating_ip(instance=inst)
            setattr(inst, "floating_ip", fip_obj.get("floating_ip_address"))
        self.resources['instances'].update({vm_id: inst})

        # QOS support
        for vm_net in vm_nets:
            if isinstance(vm_net, dict):
                qos_rules = []
                qos_ingress_limit = vm_net.get("ingress")
                qos_egress_limit = vm_net.get("egress")
                if qos_ingress_limit:
                    qos_rules.append({"direction":"ingress",
                                      "max_kbps":qos_ingress_limit,
                                      "max_burst_kbps":qos_ingress_limit})
                if qos_egress_limit:
                    qos_rules.append({"direction":"egress",
                                      "max_kbps":qos_egress_limit,
                                      "max_burst_kbps":qos_egress_limit})
                if qos_rules:
                    self.inst_add_qos_policy(vm_id, vm_net.get("name"),
                                        instance=inst, qos_rules=qos_rules)

        return inst
