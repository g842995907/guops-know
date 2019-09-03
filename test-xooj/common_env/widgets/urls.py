# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from .test_env import urls as test_env_urls


urlpatterns = [
    url(r'^test_env/', include(test_env_urls, namespace='test_env')),
]
