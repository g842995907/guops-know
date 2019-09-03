# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from .cms import api
from .cms import views

viewsets = (
    api.EventViewSet,
    api.EventSignupUserViewSet,
    api.EventSignupTeamViewSet,
    api.EventTaskViewSet,
    api.EventUserSubmitLogViewSet,
    api.EventUserAnswerViewSet,
    api.EventNoticeViewSet,
    api.EventTaskNoticeViewSet,
    api.EventRankViewSet,
)
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^exam_list/$', views.exam_list, name='exam_list'),
    url(r'^exam_list/(?P<pk>[0-9]+)/$', views.exam_detail, name='exam_detail'),
    url(r'^exam_list/(?P<pk>[0-9]+)/task_list_new/$', views.task_list_new, name='task_list'),
    url(r'^exam_list/(?P<pk>[0-9]+)/task_list/(?P<task_pk>[0-9]+)/$', views.task_detail, name='task_detail'),
    url(r'^handler_task_list/(?P<pk>[0-9]+)/$', views.handler_task_list, name='handler_task_list'),
    url(r'^eventreportscore/(?P<pk>[0-9]+)/$', views.event_report_score, name='event_report_score'),
    url(r'^achievement/(?P<pk>[0-9]+)/$', views.event_achievement, name='event_achievement'),
    url(r'^name_check/$', views.name_check, name='name_check'),

    url(r'^auth_class/(?P<exam_id>[a-z0-9]+)/$', views.auth_class, name='auth_class'),
    url(r'^share_teacher/(?P<event_id>[a-z0-9]+)/$', views.share_teacher, name='share_teacher'),

    url(r'^output/(?P<pk>[0-9]+)/$', views.outputResult, name='output'),
    url(r'^event_rank_list/$', views.event_rank_list, name='event_rank_list'),
]
