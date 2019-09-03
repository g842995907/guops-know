from __future__ import unicode_literals

import logging

from common_scene.base import BaseSceneRollbacker
from common_scene.compute.workflows.delete_flow import ServerSceneDeleter


LOG = logging.getLogger(__name__)
ATTEMPTS = 60


class ServerSceneRollbacker(ServerSceneDeleter, BaseSceneRollbacker):
    def __init__(self, *args, **kwargs):
        super(ServerSceneRollbacker, self).__init__(*args, **kwargs)
