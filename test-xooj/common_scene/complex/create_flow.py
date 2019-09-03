from __future__ import unicode_literals

import logging

from common_scene.compute.workflows.create_flow import ServerSceneCreator
from common_scene.docker.workflows.create_flow import DockerSceneCreator


LOG = logging.getLogger(__name__)


class ComplexSceneCreater(ServerSceneCreator, DockerSceneCreator):
    def __init__(self, request_id, **kwargs):
        super(ComplexSceneCreater, self).__init__(request_id, **kwargs)
