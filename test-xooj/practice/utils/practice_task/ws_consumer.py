# -*- coding: utf-8 -*-
import logging

from channels import Group
from channels.auth import channel_session_user_from_http

from practice.api import get_task_object

logger = logging.getLogger()


def get_task_user(task, user):
    return Group("user-%d-task-%s" % (user.id, task.id))


def get_task(**kwargs):
    task_hash = kwargs.get('task_hash', None)
    task = get_task_object(task_hash)
    return task


@channel_session_user_from_http
def ws_add(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_task(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    message.reply_channel.send({"accept": True})
    get_task_user(lesson, message.user).add(message.reply_channel)


@channel_session_user_from_http
def ws_message(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_task(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    get_task_user(lesson, message.user).send({
        "text": message.content['text'],
    })


@channel_session_user_from_http
def ws_disconnect(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_task(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    get_task_user(lesson, message.user).discard(message.reply_channel)
