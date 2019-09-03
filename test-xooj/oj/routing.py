# -*- coding: utf-8 -*-
import logging
import os
from importlib import import_module

from channels.routing import route
from django.conf import settings

from cloud_client.utils.update import ws_consumer as update_consumer

logger = logging.getLogger(__name__)
channel_routing = [
    route("websocket.connect", update_consumer.ws_add, path=r'^/update/websocket/state/$'),
    route("websocket.receive", update_consumer.ws_message, path=r'^/update/websocket/state/$'),
    route("websocket.disconnect", update_consumer.ws_disconnect, path=r'^/update/websocket/state/$')
]

if settings.PLATFORM_TYPE == "AD" or settings.PLATFORM_TYPE == "ALL":
    from event_attack_defense.cms.handler.checker import checker
    from event_attack_defense.cms.handler.control import control
    from event_attack_defense.cms.handler.deploy import flag, task
    from event_attack_defense.cms.handler.statistic import statistic
    from event_attack_defense.util import consumer

    from practice.utils.practice_task import ws_consumer as practice_consumer

    channel_routing.extend([
        route('push-flag', flag.push_flag_message),
        route('control', control.control_message),
        route('check', checker.check_round_message),
        route('statistic', statistic.statistic_message),
        route('task_deploy', task.deploy_team_task_message),

        route("websocket.connect", consumer.ws_add, path=r"^/ad/websocket/(?P<event_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.receive", consumer.ws_message, path=r"^/ad/websocket/(?P<event_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.disconnect", consumer.ws_disconnect, path=r"^/ad/websocket/(?P<event_hash>[0-9a-z\-\.]+)/$"),

        route("websocket.connect", consumer.public_ws_add, path=r"^/ad/public/(?P<event_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.receive", consumer.public_ws_message, path=r"^/ad/public/(?P<event_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.disconnect", consumer.public_ws_disconnect,
              path=r"^/ad/public/(?P<event_hash>[0-9a-z\-\.]+)/$"),

        route("websocket.connect", practice_consumer.ws_add, path=r'^/practice/websocket/task/(?P<task_hash>[0-9a-z\-\.]+)/$'),
        route("websocket.receive", practice_consumer.ws_message, path=r'^/practice/websocket/task/(?P<task_hash>[0-9a-z\-\.]+)/$'),
        route("websocket.disconnect", practice_consumer.ws_disconnect, path=r'^/practice/websocket/task/(?P<task_hash>[0-9a-z\-\.]+)/$'),
    ])

if settings.PLATFORM_TYPE == "OJ" or settings.PLATFORM_TYPE == 'ALL':
    from course.utils.lesson import ws_consumer as lesson_consumer

    channel_routing.extend([
        route("websocket.connect", lesson_consumer.ws_add,
              path=r"^/course/websocket/lesson/(?P<lesson_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.receive", lesson_consumer.ws_message,
              path=r"^/course/websocket/lesson/(?P<lesson_hash>[0-9a-z\-\.]+)/$"),
        route("websocket.disconnect", lesson_consumer.ws_disconnect,
              path=r"^/course/websocket/lesson/(?P<lesson_hash>[0-9a-z\-\.]+)/$"),
    ])


# 为每一个模块添加路由
for app in settings.XCTF_APPS + settings.BASE_APPS:
    full_routing_path = os.path.join(settings.BASE_DIR, app, 'routing.py')
    if os.path.exists(full_routing_path):
        routing_path = '%s.%s' % (app, 'routing')

        try:
            _app_routing = import_module(routing_path)
            app_routing = _app_routing.routing
            if not app_routing:
                continue
            channel_routing.extend(app_routing)
        except Exception, e:
            logger.info("load routing error error[%s]", str(e))
            raise e