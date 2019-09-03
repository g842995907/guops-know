from __future__ import unicode_literals

import logging
import os
import time
import urlparse

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneCreator, logger_decorator, check_kwargs
from common_scene.setting import api_settings
from common_scene.docker import params

ATTEMPTS = 60
DEFAULT_COMMAND = "sleep infinity;"
LOG = logging.getLogger(__name__)

states = {
  'ERROR': 'Error', 'RUNNING': 'Running', 'STOPPED': 'Stopped',
  'PAUSED': 'Paused', 'UNKNOWN': 'Unknown', 'CREATING': 'Creating',
  'CREATED': 'Created', 'DELETED': 'Deleted'
}


class DockerSceneCreator(BaseSceneCreator):
    def __init__(self, request_id, **kwargs):
        super(DockerSceneCreator, self).__init__(request_id, **kwargs)

    def _create_container(self, **kwargs):
        cont_id = kwargs.pop("cont_id")
        try:
            container = self.zun_cli.container_create(**kwargs)
            LOG.info("Created container {} .".format(kwargs.get("name")))
            self.resources['containers'].update({cont_id: container})
            return container
        except Exception, e:
            err_msg = _("Unable to create container {}").format(cont_id)
            self._handle_error(err_msg, e)

    def _run_container(self, **kwargs):
        cont_id = kwargs.pop("cont_id")
        try:
            container = self.zun_cli.container_create(**kwargs)
            LOG.info("Created container {} .".format(kwargs.get("name")))
            self.resources['containers'].update({cont_id: container})
            return container
        except Exception, e:
            err_msg = _("Unable to run container {}").format(cont_id)
            self._handle_error(err_msg, e)

    def _check_container_status(self, container):
        cont_id = container.id if hasattr(container, "uuid") else container

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check status for container {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(cont_id)
                break
            cont = self.zun_cli.container_show(cont_id)
            if cont.status == states['RUNNING']:
                msg = "Container {} status Running.".format(cont_id)
                LOG.info(msg)
                return cont
            elif cont.status == states['ERROR']:
                err_msg = _("Container status error. "
                            "{}").format(cont.status_reason)
                break
            LOG.debug("Instance status not active. "
                      "Try again 1 second later...")
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    def _generate_cont_user_data(self, container_id,
                            install_script=None, init_script=None):
        userdata = []
        userdata.append(params.report_status.format(
            env_id=self.request_id, vm_id=container_id, status=4,
            report_url=api_settings.COMPLEX_MISC.get("report_vm_status")))

        zip_file_name = urlparse.urlsplit(self.attach_url).path.split("/")[-1]
        file_folder = os.path.splitext(zip_file_name)[0]

        # download zip file
        userdata.append(params.download_zip.format(
            zip_file_name=zip_file_name, attach_url=self.attach_url))

        # unzip zip file
        userdata.append(params.unzip_file.format(
            zip_file_name=zip_file_name, file_folder=file_folder))

        # execute install.sh
        if install_script:
            script_path = install_script.split()[0]
            script_folder = os.path.join(file_folder,
                                         os.path.split(script_path)[0])
            userdata.append(params.change_dir.format(script_folder=script_folder))
            userdata.append(params.install_evn.format(file_folder=file_folder,
                                                      script_folder=script_folder,
                                                      init_script=init_script))

        # execute init.sh
        if init_script:
            script_path = install_script.split()[0]
            script_folder = os.path.join(file_folder,
                                         os.path.split(script_path)[0])
            userdata.append(params.change_dir.format(script_folder=script_folder))
            userdata.append(params.init_services.format(file_folder=file_folder,
                                                        script_folder=script_folder,
                                                        init_script=init_script))

        userdata.append(params.report_status.format(
            env_id=self.request_id, vm_id=container_id, status=6,
            report_url=api_settings.COMPLEX_MISC.get("report_vm_status")))
        return userdata

    def cont_add_qos_policy(self, cont_key, net_key, container, qos_rules=None):
        if not qos_rules:
            err_msg = _("No qos rules found for "
                        "container {}").format(container.name)
            LOG.debug(err_msg)
            return False

        policy_name = "{}-{}-qos".format(cont_key, net_key)
        try:
            policy = self.neutron_cli.qos_policy_create(name=policy_name)
            for rule_dict in qos_rules:
                self.neutron_cli.qos_bandwidth_limit_rule_create(
                    policy.get("id"), **rule_dict)
            self.resources["qoses"].update({cont_key: policy})
        except Exception, e:
            err_msg = _("Unable to create qos policy {}").format(policy_name)
            self._handle_error(err_msg, e)

        try:
            ports = []
            for port in ports:
                self.bind_ports_qos_policy(port.get("id"), policy.get("id"))
            return True
        except Exception, e:
            err_msg = _("Unable to bind qos policy {} "
                        "to container {}").format(policy_name, container.name)
            self._handle_error(err_msg, e)

    @logger_decorator
    @check_kwargs("id", "image")
    def create_container(self, **kwargs):
        cont_id = kwargs.get("id")
        name = kwargs.get("name")
        image = kwargs.get("image")
        command = kwargs.get("command") or DEFAULT_COMMAND

        image_type = kwargs.get("imageType", "linux").lower()
        flavor = self._get_flavor(flavor_name=kwargs.get("flavor"))
        security_groups = kwargs.get("security_groups") or \
                          self._get_security_groups()

        vm_nets = kwargs.get("net") or ['openstack']
        nics = self._analysis_networks(cont_id, vm_nets,
                                       kwargs.get("global_network"),
                                       kwargs.get("fixed_ip"))
        # generate commands
        if self.attach_url:
            init_script = kwargs.get("initScript")
            if init_script:
                init_script = self._analysis_init_script(init_script)
            user_data = self._generate_cont_user_data(
                            cont_id, kwargs.get("installScript"), init_script)
            if user_data:
                command = " && ".join(user_data.append(command))

        params = {"cont_id": cont_id, "name": name, "image": image,
                  "command": '/bin/bash -c "{}"'.format(command),
                  "security_groups": security_groups,
                  "nets": nics, "run": kwargs.get("run", True)}
        if flavor:
            params.update({"cpu": flavor.vcpus, "memory": flavor.ram})

        container = self._create_container(**params)
        container = self._check_container_status(container)

        # init container
        # self.init_container(container.get("id"),
        #                     kwargs.get("install_cmd"),
        #                     self._analysis_init_script(kwargs.get("init_cmd")))

        # associate floating ip
        vm_role = kwargs.get("role")
        if self._need_floating_ip(vm_role):
            port_id = None
            for net_id, subnets in container.addresses.items():
                port_id = subnets[0].get("port")
            fip_obj = self.bind_floating_ip(port=port_id)
            setattr(container, "floating_ip", fip_obj.get("floating_ip_address"))
        self.resources['containers'].update({id: container})

        # TODO: add QOS support
        # for vm_net in vm_nets:
        #     if isinstance(vm_net, dict):
        #         qos_rules = []
        #         qos_ingress_limit = vm_net.get("ingress")
        #         qos_egress_limit = vm_net.get("egress")
        #         if qos_ingress_limit:
        #             qos_rules.append({"direction":"ingress",
        #                               "max_kbps":qos_ingress_limit,
        #                               "max_burst_kbps":qos_ingress_limit})
        #         if qos_egress_limit:
        #             qos_rules.append({"direction":"egress",
        #                               "max_kbps":qos_egress_limit,
        #                               "max_burst_kbps":qos_egress_limit})
        #         if qos_rules:
        #             self.cont_add_qos_policy(cont_id, vm_net.get("name"),
        #                                      container, qos_rules=qos_rules)

        return container

    @logger_decorator
    def copy_file(self, **kwargs):
        pass

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

    def _report_container_status(self, container_id, status):
        report_cmd = params.report_status.format(
            env_id=self.request_id, vm_id=container_id, status=status,
            report_url=api_settings.COMPLEX_MISC.get("report_vm_status"))
        resp = self.execute_command(container_id, command=report_cmd)

    @logger_decorator
    def init_container(self, container_id, **kwargs):
        # status change to started
        self._report_container_status(container_id, 4)
        attach_url = ""
        zip_file_name = urlparse.urlsplit(attach_url).path.split("/")[-1]
        file_folder = os.path.splitext(zip_file_name)[0]

        # download zip from oj
        download_cmd = params.download_zip.format()
        resp = self.execute_command(container_id, command=download_cmd)
        script_folder = ""
        zip_file_name = ""
        file_folder = ""

        # execute init script
        install_cmd = params.install_evn.format(kwargs.get("install_cmd"))
        resp = self.execute_command(container_id, command=install_cmd)

        # execute init script
        init_cmd = params.init_services.format(kwargs.get("init_cmd"))
        resp = self.execute_command(container_id, command=init_cmd)

        # delete zip file if not debug
        if api_settings.COMPLEX_MISC.get("clean_env", False):
            params.clean_env.format(file_folder=file_folder)

        # status change to running
        self._report_container_status(container_id, 6)

        return True

    @logger_decorator
    def execute_command(self, container_id, **kwargs):
        command = kwargs.get("command")
        try:
            return self.zun_cli.container_execute(container_id, command)
        except Exception, e:
            err_msg = _("Unable to execute command {}").format(command)
            self._handle_error(err_msg, e)

    def create(self):
        pass
