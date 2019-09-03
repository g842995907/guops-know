# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from common_auth import viewset

viewsets = (
    viewset.FacultyViewSet,
    viewset.MajorViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
]
