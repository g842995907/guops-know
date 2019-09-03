# -*- coding: utf-8 -*-
import base64
import logging

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from common_web.decorators import login_required as web_login_required
from common_framework.views import find_menu
from practice.api import get_task_object, TYPE_NAME_MAP
from practice.setting import api_settings
from practice.utils.user_action import ua

from common_framework.models import AuthAndShare
from functools import wraps


def get_auth_practice(func):
    @wraps(func)
    def check_auth(request, *args, **kwargs):
        user = request.user
        practice = get_task_object(kwargs.get('task_hash'))
        practice_event = practice.event

        if not user.is_superuser and not practice_event.create_user == user:
            if not practice_event.auth == AuthAndShare.AuthMode.ALL_AUTH_MODE:
                if user.faculty not in practice_event.auth_faculty.all() and user.major not in practice_event.auth_major.all() and user.classes not in practice_event.auth_classes.all():
                    return render(request, 'web/404.html', context={})
        return func(request, *args, **kwargs)
    return check_auth


logger = logging.getLogger()
slug = api_settings.SLUG


@web_login_required
@find_menu(slug)
@get_auth_practice
def task_detail(request, typeid, task_hash, **kwargs):
    context = {
        'menu': kwargs.get('menu').get('menu'),
        'type_id': typeid,
        'task_hash': task_hash,
    }
    knowledges_list = None
    if int(typeid) == 0:
        task = get_task_object(task_hash)
        if task.knowledges:
            knowledges_list = task.knowledges.split(",")
        ua.practice_task(
            request.user,
            type=_(TYPE_NAME_MAP[int(typeid)]),
            task=task.content,
        )
        context.update({
            'knowledges_list':knowledges_list,
        })
        return render(request, 'practice/web/do_task.html', context)
    else:
        from common_env.models import Env
        task = get_task_object(task_hash)
        if task.knowledges:
            knowledges_list = task.knowledges.split(",")
        ua.practice_task(
            request.user,
            type=_(TYPE_NAME_MAP[int(typeid)]),
            task=task.title,
        )
        task_env = task.envs.filter(
            env__status__in=Env.ActiveStatusList,
            env__user=request.user
        ).first()
        context.update({
            'task': task,
            'task_env': task_env,
            'markdown': task.markdown,
            'knowledges_list': knowledges_list,
        })
        return render(request, 'practice/web/do_task2.html', context)


@web_login_required
def task_network(request, typeid, task_hash):
    context = {}
    url = request.GET.get('url', '')
    if url == '':
        raise Exception('url not find')
    task = get_task_object(task_hash)
    context['task'] = task
    context['guacamole_url'] = url
    context['task_hash'] = task_hash
    context['type_id'] = str(typeid)

    return render(request, 'practice/web/practice_network.html', context)


@web_login_required
@find_menu(slug)
def markdown(request, **kwargs):
    context = kwargs.get('menu')
    # type_id = request.GET.get("type_id")
    task_hash = request.GET.get("task_hash")
    if task_hash:
        task = get_task_object(task_hash)
        wp_base64 = base64.b64encode(task.official_writeup)
        context.update({"markdown": wp_base64})
    return render(request, 'practice/web/markdown.html', context)
