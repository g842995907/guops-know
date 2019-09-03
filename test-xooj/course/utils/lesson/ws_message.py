import json

from common_framework.utils.enum import enum

from . import ws_consumer


MESSAGE_CODE = enum(
    CONVERTED=10000,
)


def send_lesson_user_data(lesson, user, message_type, message_data=None):
    ws_consumer.get_lesson_user(lesson, user).send({
        "text": json.dumps({
            'type': message_type,
            'data': message_data,
        }),
    })


