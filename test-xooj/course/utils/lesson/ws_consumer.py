# -*- coding: utf-8 -*-
import logging

from channels import Group
from channels.auth import channel_session_user_from_http

from course.models import Lesson


logger = logging.getLogger()


def get_lesson_user(lesson, user):
    return Group("user-%d-lesson-%s" % (user.id, lesson.id))


def get_lesson(**kwargs):
    lesson_hash = kwargs.get('lesson_hash', None)
    lesson = Lesson.objects.filter(hash=lesson_hash).first()
    return lesson


@channel_session_user_from_http
def ws_add(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_lesson(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    message.reply_channel.send({"accept": True})
    get_lesson_user(lesson, message.user).add(message.reply_channel)


@channel_session_user_from_http
def ws_message(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_lesson(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    get_lesson_user(lesson, message.user).send({
        "text": message.content['text'],
    })


@channel_session_user_from_http
def ws_disconnect(message, **kwargs):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    lesson = get_lesson(**kwargs)
    if not lesson:
        message.reply_channel.send({"close": True})
        return

    get_lesson_user(lesson, message.user).discard(message.reply_channel)
