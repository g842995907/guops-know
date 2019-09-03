from __future__ import unicode_literals

import logging

from common_scene.compute.workflows.template_flow import ServerSceneTemplater
from common_scene.docker.workflows.template_flow import DockerSceneTemplater


LOG = logging.getLogger(__name__)


class ComplexSceneTemplater(ServerSceneTemplater, DockerSceneTemplater):
    def __init__(self, *args, **kwargs):
        super(ComplexSceneTemplater, self).__init__(*args, **kwargs)
