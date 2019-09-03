# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from .env import urls as task_env_urls
from .ad_env import urls as ad_env_urls


urlpatterns = [
    url(r'^task_env/', include(task_env_urls, namespace='task_env')),
    url(r'^ad_env/', include(ad_env_urls, namespace='ad_env')),
]
