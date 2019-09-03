
import re

from .base import Websocket


def get_routers(websocket_classes, namespace):
    routers = []
    for websocket_class in websocket_classes:
        names = re.findall(r'[A-Z][a-z]+', websocket_class.__name__)
        common_prefix = names[-1].lower()
        names = [s.lower() for s in names[:-1]]
        name = '_'.join(names)
        path = '/{}/{}/{}'.format(namespace, common_prefix, name)
        routers.append(websocket_class.as_new_route(path))
    return routers