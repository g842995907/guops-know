# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from .web import api
from .web import views


viewsets = (
    api.EventViewSet,
    
    api.EventSignupTeamActivityViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^list/$', views.list, name='list'),
    url(r'^detail/$', views.detail, name='detail'),
]
