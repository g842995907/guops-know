import json

from common_framework.utils.enum import enum

from . import ws_consumer


MESSAGE_CODE = enum(
    CONVERTED=10000,
)


def send_task_user_data(task, user, message_type, message_data=None):
    ws_consumer.get_task_user(task, user).send({
        "text": json.dumps({
            'type': message_type,
            'data': message_data,
        }),
    })


