# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from . import api


urlpatterns = [
    url(r'^lesson_env/$', api.lesson_env, name='lesson_env'),
    url(r'^recover_lesson_env/$', api.recover_lesson_env, name='recover_lesson_env'),
    url(r'^deplay_lesson_env/$', api.deplay_lesson_env, name='deplay_lesson_env'),
]

