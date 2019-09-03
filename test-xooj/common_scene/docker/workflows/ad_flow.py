from __future__ import unicode_literals

import logging

from common_scene.base import BaseADSceneCreator, BaseADSceneDeleter
from common_scene.docker.workflows.create_flow import DockerSceneCreator
from common_scene.docker.workflows.delete_flow import DockerSceneDeleter


LOG = logging.getLogger(__name__)


class DockerADSceneCreator(BaseADSceneCreator, DockerSceneCreator):
    def __init__(self, contest_id, **kwargs):
        super(DockerADSceneCreator, self).__init__(contest_id, **kwargs)


class DockerADSceneDeleter(BaseADSceneDeleter, DockerSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(DockerADSceneDeleter, self).__init__(*args, **kwargs)
