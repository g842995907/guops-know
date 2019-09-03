# -*- coding: utf-8 -*-
from functools import partial

from system_configuration.models import UserAction
from system_configuration.cms.api import UserActionViewSet


def add_user_action(user, content, extra=''):
    last_ua = UserAction.objects.filter(user=user).last()
    if last_ua and last_ua.content == content:
        return

    UserAction.objects.create(user=user, content=content, extra=extra)
    UserActionViewSet.clear_self_cache()


def _add_user_action(template, user, **params):
    extra = params.pop('_extra', '')
    content = template.format(**params)
    add_user_action(user, content, extra)


def get_ua(ua_template):
    ua = type('UA', (object,), {})
    for func_name, template in ua_template.source.items():
        setattr(ua, func_name.lower(), partial(_add_user_action, template))

    return ua