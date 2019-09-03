
from common_framework.utils.websocket import get_routers

from .widgets.test_env import websocket as test_env_websocket


routing = get_routers([
    # test_env_websocket.TestEnvWebsocket
], namespace='common_env')


