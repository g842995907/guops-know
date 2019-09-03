# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from system_configuration.web import api

viewsets = (
    api.SystemConfigurationViewSet,
    api.SysNoticeViewSet,
    api.UserNoticeViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
]
