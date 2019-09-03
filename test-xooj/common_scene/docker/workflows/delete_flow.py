from __future__ import unicode_literals

import logging
import time

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneDeleter, logger_decorator
from common_scene.clients.zun_client import Client as zun_client


LOG = logging.getLogger(__name__)
ATTEMPTS = 60


class DockerSceneDeleter(BaseSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(DockerSceneDeleter, self).__init__(*args, **kwargs)
        self.zun_cli = zun_client()

    @logger_decorator
    def delete_container(self, container_id):
        try:
            self.zun_cli.container_delete(container_id, force=True)
            LOG.info("Deleting container {} ...".format(container_id))
        except Exception, e:
            err_msg = _("Unable to delete container {}.").format(container_id)
            LOG.error(err_msg)
            LOG.error(e)

        attempts = ATTEMPTS
        while attempts:
            try:
                self.zun_cli.container_show(container_id)
            except Exception, e:
                LOG.info("Deleted container {}".format(container_id))
                break
            attempts -= 1
            time.sleep(1)

    @logger_decorator
    def delete_network(self, network_id):
        try:
            subnets = self.neutron_cli.subnet_get_all(network_id=network_id)
            for subnet in subnets:
                self._sync_cidr(subnet.get("cidr"))
        except Exception, e:
            err_msg = _("Unable to get network subnets {}.").format(network_id)
            LOG.error(err_msg)
            LOG.error(e)

        super(DockerSceneDeleter, self).delete_network(network_id)
