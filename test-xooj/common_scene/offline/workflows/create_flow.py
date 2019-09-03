from __future__ import unicode_literals

import functools
import logging
import uuid

from django.utils.translation import ugettext as _

from common_scene.compute.views import InstanceAction
from common_scene.image.views import ImageAction
from common_scene.network.views import NetworkAction


LOG = logging.getLogger(__name__)


class OfflineSceneCreator(InstanceAction, ImageAction, NetworkAction):
    def __init__(self, *args, **kwargs):
        super(OfflineSceneCreator, self).__init__(*args, **kwargs)

    def create_team_task_vm(self, **kwargs):
        team_id = kwargs.get("team_id")
        task_id = kwargs.get("task_id")
        vm_ip = kwargs.get("address")
        image = kwargs.get("image")
        host = kwargs.get("host")

    def create_task_template_vm(self, **kwargs):
        image = kwargs.get("image")

        if not image:
            err_msg = _("Param image must be configured. "
                        "kwargs: {}").format(kwargs)

        vm_ip = kwargs.get("address")
        host = kwargs.get("host")
