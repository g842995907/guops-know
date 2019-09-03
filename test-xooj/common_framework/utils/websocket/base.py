# -*- coding: utf-8 -*-
import re

from channels.routing import route, route_class

from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer


class Websocket(JsonWebsocketConsumer):

    http_user_and_session = True

    path_name = ''

    @classmethod
    def as_new_route(cls, path):
        route_path = path
        if cls.path_name:
            route_path = path + '/' + cls.path_name
        return cls.as_route(path=route_path)
