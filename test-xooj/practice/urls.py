# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from practice.web import api

from common_framework.utils.rest.routers import get_default_router

from practice import api as practice_api
import views

viewsets = (
    api.PracticeRankViewSet,
)

router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    # 根据类型获取习题集
    url(r'^rest/event/$', practice_api.http_get_task_event_by_type, name='event_list'),

    # 获取习题集详情
    url(r'^rest/event/(?P<event_id>[0-9]+)/$', practice_api.http_get_event_detail, name='event_detail'),

    # 根据习题集获取题目列表
    url(r'^rest/task/$', practice_api.http_get_task_list, name='task_list'),

    # 根据hash获取题目详情
    url(r'^rest/task_detail/$', practice_api.http_gettask_detail, name='task_detail'),

    # 提交答案
    url(r'^rest/score/$', practice_api.commit_task_answer, name='score_list'),

    # 根据习题集获取题目Id列表
    url(r'^rest/task_hash/$', practice_api.http_gettask_hash_list, name='task_hash_list'),

    # 题目详情
    url(r'^task/$', views.task_detail, name='defensetraintaskTT'),
    url(r'^task/(?P<typeid>[0-9]+)/$', views.task_detail, name='defensetraintaskT'),
    url(r'^task/(?P<typeid>[0-9]+)/(?P<task_hash>[a-z-0-9]+.[0-9]+)/$', views.task_detail,
        name='defensetraintask'),
    # 显示跳转到新版的guacamole详情页面
    url(r'task/network/(?P<typeid>[0-9]+)/(?P<task_hash>[a-z-0-9]+.[0-9]+)/$', views.task_network, name='task_network'),
    # writeup 显示为markdown的形式
    url(r'task/markdown', views.markdown, name='practice_markdown'),

    # 获取个人答题情况
    url(r'^rest/get_personal_task_record/$', practice_api.get_personal_task_record, name='get_personal_task_record'),

    # 获取个人某道题答题记录
    url(r'^rest/get_personal_task_record/(?P<task_hash>[a-z-0-9]+.[0-9]+)/$', practice_api.get_task_record_detail,
        name='task_record_detail'),

    # 获取类型种类
    url(r'^rest/task_category/$', practice_api.http_task_category, name='category_list'),

    # 个人技能六维图
    url(r'^rest/get_radar_data/$', practice_api.http_get_radar_data, name='task_radar_data'),

    url(r'^rest/env_servers/$', practice_api.http_get_env_servers, name='env_servers'),
]
