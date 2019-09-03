from __future__ import unicode_literals

import logging

from common_scene.base import BaseSceneRollbacker
from common_scene.docker.workflows.delete_flow import DockerSceneDeleter


LOG = logging.getLogger(__name__)
ATTEMPTS = 60


class DockerSceneRollbacker(DockerSceneDeleter, BaseSceneRollbacker):
    def __init__(self, *args, **kwargs):
        super(DockerSceneRollbacker, self).__init__(*args, **kwargs)
