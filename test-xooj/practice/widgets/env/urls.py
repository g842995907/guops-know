# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from . import api


urlpatterns = [
    url(r'^task_env/$', api.task_env, name='task_env'),
    url(r'^recover_task_env/$', api.recover_task_env, name='recover_task_env'),
    url(r'^delay_task_env/$', api.delay_task_env, name='delay_task_env'),
]

