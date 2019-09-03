# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router
from practice_man_machine.cms import api as cms_api
from practice_man_machine.cms import views

viewsets = [
    cms_api.ManMachineTaskViewSet,
    cms_api.ManMachineCategoryViewSet
]
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='cms_api')),
    url(r'^task_list/$', views.task_list, name='task_list'),
    url(r'^task_list/(?P<pk>[0-9]+)$', views.task_detail, name='task_detail'),
    url(r'^category_list/$', views.category_list, name='category_list'),
    url(r'^categories/(?P<category_id>[^/.]+)/detail/$', views.category_detail, name='category_detail'),
    url(r'^categories/create/$', views.category_create, name='category_create'),

    # url(r'^exam/$', views.exam, name='exam'),
]
