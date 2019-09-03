# -*- coding: utf-8 -*-

import logging

from django.shortcuts import render

from common_framework.views import find_menu

from common_web.decorators import login_required as web_login_required

from practice import api as practice_api
from practice_exercise.setting import api_settings

logger = logging.getLogger()
slug = api_settings.SLUG


@web_login_required
@find_menu(slug)
def web_event_list(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'practice/web/event_list.html', context)


@web_login_required
@find_menu(slug)
def task_list(request, event_id, **kwargs):
    type_id = practice_api.PRACTICE_TYPE_EXCRISE
    event_id = event_id
    context = {
        'active_menus': kwargs.get('menu').get('active_menus'),
        'menu': kwargs.get('menu').get('menu'),
        'type_id': type_id,
        'event_id': event_id,
    }
    return render(request, 'practice/web/task_list.html', context)


@web_login_required
@find_menu(slug)
def do_task(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'practice/web/do_task.html', context)


@web_login_required
@find_menu(slug)
def do_task2(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'practice/web/do_task2.html', context)
