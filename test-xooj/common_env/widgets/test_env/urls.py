# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from . import api


urlpatterns = [
    url(r'^test_env/$', api.test_env, name='test_env'),
]

