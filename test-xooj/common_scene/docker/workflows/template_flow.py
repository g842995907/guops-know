from __future__ import unicode_literals

import logging
import os
import threading
import urlparse
import uuid

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneTemplater
from common_scene.docker import params
from common_scene.docker.views import ContainerAction
from common_scene.image.views import ImageAction
from common_scene.network.views import NetworkAction
from common_scene.setting import api_settings
from common_scene import utils as project_utils

LOG = logging.getLogger(__name__)
ATTEMPTS = 60
SNAPAHOT_PREFIX = "snapshot"
WINDOWS = "windows"
LINUX = "linux"


class DockerSceneTemplater(BaseSceneTemplater, ContainerAction, ImageAction, NetworkAction):
    def __init__(self, *args, **kwargs):
        super(DockerSceneTemplater, self).__init__(*args, **kwargs)
        self.request_id = args[0]
        self.containers = {}
        self.snapshots = []

    def _generate_user_data(self, container_id,
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
        root_pwd = str(uuid.uuid4())[:8]
        userdata.append(params.change_root_pwd.format(root_pwd=root_pwd))

        userdata.append(params.report_status.format(
            env_id=self.request_id, vm_id=container_id, status=6,
            report_url=api_settings.COMPLEX_MISC.get("report_vm_status")))
        return userdata, root_pwd

    def create_template_container(self, **kwargs):
        cont_key = kwargs.get("id")
        image = self.get_image(name=kwargs.get("image"))
        if not image:
            err_msg = _("Unable to get image by '{}'").format(kwargs.get("image"))
            LOG.error(err_msg)
            raise Exception(err_msg)

        cont_name = kwargs.get("name") or "template-{}".format(str(uuid.uuid4())[:8])
        command = kwargs.get("command")
        nics = [{"net-id": api_settings.COMPLEX_MISC.get("template_net"),
                 "v4-fixed-ip": kwargs.get("ip_address") or ""}]

        # flavor
        image_type = kwargs.get("image_type")
        flavor = self._get_flavor(kwargs.get("flavor"), image_type)

        params = {"cont_id": cont_name, "name": cont_name, "image": image,
                  "command": command,
                  "security_groups": kwargs.get("security_groups"),
                  "nets": nics, "run": kwargs.get("run", True)}
        if flavor:
            params.update({"cpu": flavor.vcpus, "memory": flavor.ram})

        # generate commands
        if self.attach_url:
            user_data, root_pwd = self._generate_user_data(cont_key)
            if user_data:
                command = " && ".join(user_data.append(command))

        try:
            container = self.zun_cli.container_create()
            fip = self.bind_fip(fip=self.generate_fip(), port=container.addresses.values[0])
            setattr(container, "floating_ip", fip.get("floating_ip_address"))
            setattr(container, "username", "root")
            setattr(container, "root_pwd", root_pwd)
            self.containers.update({kwargs.get("name"): container})
            return container
        except Exception, e:
            err_msg = "Unable to create container: {}.".format(cont_name)
            LOG.error(err_msg)
            LOG.error(e)
        raise Exception(err_msg)

    def snapshot_template_container(self, **kwargs):
        cont_key = kwargs.pop("cont_key")
        snapshot_id = self.save_image(cont_key,
                                           kwargs.get("snapshot_name"))
        self.snapshots.append(snapshot_id)
        if kwargs.get("report_status"):
            threading.Thread(target=self.report_image_status, args=(snapshot_id,))

    def delete_template_container(self, container_id):
        self.delete_container(container_id)
