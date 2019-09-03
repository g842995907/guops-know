# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from event.cms import views as cms_views


viewsets = [

]
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^vis_contrl', cms_views.vis_control, name='vis_control'),
]