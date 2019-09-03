from __future__ import unicode_literals

import logging

from common_scene.base import BaseADSceneCreator, BaseADSceneDeleter
from common_scene.compute.workflows.create_flow import ServerSceneCreator
from common_scene.compute.workflows.delete_flow import ServerSceneDeleter


LOG = logging.getLogger(__name__)


class ServerADSceneCreator(BaseADSceneCreator, ServerSceneCreator):
    def __init__(self, contest_id, **kwargs):
        super(ServerADSceneCreator, self).__init__(contest_id, **kwargs)


class ServerADSceneDeleter(BaseADSceneDeleter, ServerSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(ServerSceneDeleter, self).__init__(*args, **kwargs)
