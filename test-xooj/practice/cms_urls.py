# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router
from practice.cms import api as cms_api
from practice.cms import views
from practice import api as practice_api

viewsets = [
    cms_api.TaskEventViewSet
]
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='cms_api')),

    url(r'^event_list/$', views.event_list, name='event_list'),
    url(r'^event_list/(?P<pk>[0-9]+)/$', views.event_detail, name='event_detail'),

    url(r'^auth_class/(?P<event_id>[a-z0-9]+)/$', views.auth_class, name='auth_class'),
    url(r'^share_teacher/(?P<event_id>[a-z0-9]+)/$', views.share_teacher, name='share_teacher'),

    url(r'^practice_categories/(?P<type_id>[a-z0-9]+)/$', views.practice_categories, name='practice_categories'),
    url(r'^rest/event/$', practice_api.http_get_task_event_by_type, name='api_event_list'),
    url(r'^rest/env_servers/$', practice_api.http_get_env_servers, name='env_servers'),
]


from practice.widgets import urls as widgets_urls

urlpatterns += [
    url(r'^widgets/', include(widgets_urls, namespace='widgets')),
]