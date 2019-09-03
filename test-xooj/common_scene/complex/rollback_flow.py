from __future__ import unicode_literals

import logging

from common_scene.compute.workflows.rollback_flow import ServerSceneRollbacker
from common_scene.docker.workflows.rollback_flow import DockerSceneRollbacker


LOG = logging.getLogger(__name__)


class ComplexSceneRollbacker(ServerSceneRollbacker, DockerSceneRollbacker):
    def __init__(self, *args, **kwargs):
        super(ComplexSceneRollbacker, self).__init__(*args, **kwargs)
