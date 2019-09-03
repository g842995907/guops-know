from __future__ import unicode_literals

import logging
import threading
import uuid

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneTemplater
from common_scene.compute import params
from common_scene.compute.views import InstanceAction
from common_scene.image.views import ImageAction
from common_scene.network.views import NetworkAction
from common_scene.setting import api_settings
from common_scene import utils as project_utils

LOG = logging.getLogger(__name__)
ATTEMPTS = 60
SNAPAHOT_PREFIX = "snapshot"
WINDOWS = "windows"
LINUX = "linux"


class ServerSceneTemplater(BaseSceneTemplater, InstanceAction, ImageAction, NetworkAction):
    def __init__(self, *args, **kwargs):
        super(ServerSceneTemplater, self).__init__(*args, **kwargs)
        self.request_id = args[0]
        self.servers = {}
        self.snapshots = []

    def _generate_user_data(self, request_id, image_type):
        report_url = api_settings.COMPLEX_MISC.get("report_template_vm_status").format(request_id)
        if image_type.lower() == WINDOWS:
            userdata = params.powershell_start

            # status change to started
            userdata += params.windows_send_message2oj_template_vm.format(report_url=report_url)

            admin_pwd = project_utils.generate_complex_str()
            userdata += params.windows_change_user_pwd.format(username="administrator", password=admin_pwd)

            # delete zip file if not debug
            if api_settings.COMPLEX_MISC.get("clean_env", False):
                userdata += params.windows_clean_log.format()

            # status change to running
            userdata += params.windows_send_message2oj_template_vm.format(report_url=report_url)
            return userdata, admin_pwd
        elif image_type.lower() == LINUX:
            userdata = params.user_data_start
            # change root password
            root_pwd = project_utils.get_random_string(length=12)
            userdata += params.change_root_pwd.format(root_pwd=root_pwd)

            # custom shell script start
            userdata += params.script_block_start

            # status change to started
            userdata += params.send_message2oj_template_vm.format(report_url=report_url)

            # delete zip file if not debug
            if api_settings.COMPLEX_MISC.get("clean_env", False):
                userdata += params.clean_log.format()

            # status change to running
            userdata += params.send_message2oj_template_vm.format(report_url=report_url)

            # user data end line
            userdata += params.user_data_end
            return userdata, root_pwd
        return None, None

    def create_template_server(self, **kwargs):
        image_obj = self.get_image(name=kwargs.get("image"))
        if not image_obj:
            err_msg = _("Unable to get image by '{}'").format(kwargs.get("image"))
            LOG.error(err_msg)
            raise Exception(err_msg)

        inst_name = kwargs.get("name") or "template-{}".format(str(uuid.uuid4())[:8])
        net_ids = [{"net-id": api_settings.COMPLEX_MISC.get("template_net"),
                    "v4-fixed-ip": kwargs.get("ip_address") or ""}]

        # flavor
        image_type = kwargs.get("image_type")
        flavor = self._get_flavor(kwargs.get("flavor"), image_type)
        avail_zone = kwargs.get("avail_zone")

        # user data
        user_data, root_pwd = self._generate_user_data(self.request_id, image_type)

        security_groups = api_settings.COMPLEX_MISC.get("security_groups", ["default"])
        key_name = api_settings.COMPLEX_MISC.get("key_name")

        try:
            server = self.nova_cli.instance_create(inst_name,
                                                  image_obj,
                                                  flavor,
                                                  key_name=key_name,
                                                  user_data=user_data,
                                                  security_groups=security_groups,
                                                  nics=net_ids,
                                                  availability_zone=avail_zone)
            inst = self.check_server_status(server)
            fip = self.bind_fip(fip=self.generate_fip(), instance=inst)
            setattr(inst, "floating_ip", fip.get("floating_ip_address"))
            setattr(inst, "username", "administrator" if image_type == "windows" else "root")
            setattr(inst, "root_pwd", root_pwd)
            self.servers.update({kwargs.get("name"):inst})
            return inst
        except Exception as e:
            err_msg = "Unable to create instance: {}\n {}".format(inst_name, e)
            LOG.error(err_msg)

        raise Exception(err_msg)

    def snapshot_template_server(self, **kwargs):
        srv_key = kwargs.pop("srv_key")
        snapshot_id = self.create_snapshot(srv_key,
                                           kwargs.get("snapshot_name"))
        self.snapshots.append(snapshot_id)
        if kwargs.get("report_status"):
            threading.Thread(target=self.report_image_status,
                             args=(snapshot_id,))

    def delete_template_server(self, server_id):
        self.delete_instance(server_id)
