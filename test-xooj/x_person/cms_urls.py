# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router
from x_person.cms import api as cms_api
from x_person.cms import views

viewsets = [
    cms_api.UserViewSet,
    cms_api.TeamViewSet,
    cms_api.TeamUserViewSet,
    cms_api.FacultyViewSet,
    cms_api.MajorViewSet,
    cms_api.ClassesViewSet,
    cms_api.GroupViewSet,
]
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='cms_api')),

    url(r'^user_list/$', views.user_list, name='user_list'),
    url(r'^user_list/(?P<pk>[0-9]+)/$', views.user_detail, name='user_detail'),
    url(r'^user_audit/(?P<pk>[0-9]+)/$', views.user_audit, name='user_audit'),
    url(r'^organization/$', views.organization, name='organization'),
    url(r'^team_list/$', views.team_list, name='team_list'),
    url(r'^team_list/(?P<pk>[0-9]+)/$', views.team_detail, name='team_detail'),
    url(r'^group_list/$', views.group_list, name='group_list'),
    url(r'^group_list/(?P<pk>[0-9]+)/$', views.group_detail, name='group_detail'),
    url(r'^multi_users/$', views.multi_users, name='multi_users'),
    # url(r'^exam/$', views.exam, name='exam'),
]
