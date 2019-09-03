from __future__ import unicode_literals

import logging
import time

from django.utils.translation import ugettext as _

from common_scene.base import BaseSceneDeleter, logger_decorator
from common_scene.clients.nova_client import Client as nv_client


LOG = logging.getLogger(__name__)
ATTEMPTS = 60


class ServerSceneDeleter(BaseSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(ServerSceneDeleter, self).__init__(*args, **kwargs)
        self.nova_cli = nv_client()

    @logger_decorator
    def delete_server(self, server_id):
        try:
            self.nova_cli.instance_delete(server_id)
            LOG.info("Deleting instance {} ...".format(server_id))
        except Exception, e:
            err_msg = _("Unable to delete instance {}.").format(server_id)
            LOG.error(err_msg)
            LOG.error(e)
            return False

        attempts = ATTEMPTS
        while attempts:
            try:
                self.nova_cli.instance_get_by_id(server_id)
            except Exception, e:
                LOG.info("Deleted instance {}".format(server_id))
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

        super(ServerSceneDeleter, self).delete_network(network_id)