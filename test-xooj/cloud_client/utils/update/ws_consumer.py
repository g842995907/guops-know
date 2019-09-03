# -*- coding: utf-8 -*-
import logging

from django.core.cache import cache
from channels.auth import channel_session_user_from_http

logger = logging.getLogger()


@channel_session_user_from_http
def ws_add(message):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    state = cache.get('update-state')
    if state is None:
        cache.set('update-state', 'Preparing')
        state = 'Preparing'

    if state != 'updateEnd':
        message.reply_channel.send({"accept": True, "text": state})
    else:
        message.reply_channel.send({"close": True})


@channel_session_user_from_http
def ws_message(message):
    # if not message.user.is_authenticated:
    #     message.reply_channel.send({"close": True})
    #     return
    state = cache.get('update-state')
    if state is None:
        state = 'updateEnd'

    if state != 'updateEnd':
        message.reply_channel.send({"accept": True, "text": state})
    else:
        message.reply_channel.send({"close": True})


@channel_session_user_from_http
def ws_disconnect(message):
    if not message.user.is_authenticated:
        message.reply_channel.send({"close": True})
        return

    message.reply_channel.send({"text": "disconnect"})
