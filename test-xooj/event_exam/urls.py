# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from .web import api
from .web import views

viewsets = (
    api.EventViewSet,
    api.EventSignupUserViewSet,
    api.EventSignupTeamViewSet,
    api.EventTaskViewSet,
    api.EventUserSubmitLogViewSet,
    api.EventUserAnswerViewSet,
    api.EventNoticeViewSet,
    api.EventTaskNoticeViewSet,
)
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^list/$', views.list, name='list'),
    url(r'^list_new/$', views.list_new, name='list_new'),
    url(r'^(?P<pk>[0-9]+)/detail/$', views.detail, name='detail'),
    url(r'^exam/$', views.exam, name='exam'),
    url(r'^(?P<pk>[0-9]+)/review/$', views.review, name='review'),
    url(r'^update_status/(?P<pk>[0-9]+)/$', views.update_status, name='update_status'),

]
