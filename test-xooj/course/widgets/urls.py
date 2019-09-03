# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from .env import urls as lesson_env_urls


urlpatterns = [
    url(r'^lesson_env/', include(lesson_env_urls, namespace='lesson_env')),
]
