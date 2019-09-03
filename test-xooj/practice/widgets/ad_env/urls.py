# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from . import api


urlpatterns = [
    url(r'^task_env/$', api.task_env, name='task_env'),
    url(r'^envterminal/$', api.envterminal, name='envterminal'),
    url(r'^execute_script/$', api.execute_script, name='execute_script'),
]
