from __future__ import unicode_literals

import logging

from common_scene.compute.workflows.delete_flow import ServerSceneDeleter
from common_scene.docker.workflows.delete_flow import DockerSceneDeleter


LOG = logging.getLogger(__name__)


class ComplexSceneDeleter(ServerSceneDeleter, DockerSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(ComplexSceneDeleter, self).__init__(*args, **kwargs)
