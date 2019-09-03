from __future__ import unicode_literals

import logging

from common_scene.compute.workflows.ad_flow import ServerADSceneCreator, ServerADSceneDeleter
from common_scene.docker.workflows.ad_flow import DockerADSceneCreator, DockerADSceneDeleter

LOG = logging.getLogger(__name__)


class ComplexADSceneCreator(ServerADSceneCreator, DockerADSceneCreator):
    def __init__(self, contest_id, **kwargs):
        super(ComplexADSceneCreator, self).__init__(contest_id, **kwargs)


class ComplexADSceneDeleter(ServerADSceneDeleter, DockerADSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(ComplexADSceneDeleter, self).__init__(*args, **kwargs)
