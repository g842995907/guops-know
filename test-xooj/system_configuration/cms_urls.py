# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from common_framework.utils.rest.routers import get_default_router
from system_configuration.cms import views
from cms import api as cms_api

viewsets = [
    cms_api.SystemConfigurationViewSet,
    cms_api.BackupViewSet,
    cms_api.FactoryResetViewSet,
    cms_api.RunLogViewSet,
    cms_api.SystemLogViewSet,
    cms_api.OperationLogViewSet,
    cms_api.SysNoticeViewSet,
    cms_api.UserActionViewSet,
]
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='cms_api')),
    url(r'^system_configuration/$', views.system_configuration, name='system_configuration'),
    url(r'^license/$', views.get_license, name='license'),
    url(r'^backup/$', views.backup_list, name='backup_list'),
    url(r'^factory_reset/$', views.factory_reset, name='factory_reset'),
    url(r'^captcha/$', views.captcha, name='captcha'),
    url(r'^operation_services/$', views.operation_services, name='operation_services'),
    url(r'^hander_services_ssh/$', views.hander_services_ssh, name='hander_services_ssh'),
    url(r'^run_log/$', views.run_log, name='run_log'),
    url(r'^down_log/$', views.down_log, name='down_log'),

    url(r'^log/$', views.log, name='log'),
    url(r'^module/$', views.module, name='module'),
    url(r'^sys_notice_list/$', views.sys_notice_list, name='sys_notice_list'),
    url(r'^sys_notice_list/(?P<pk>[a-z|0-9]+)/$',views.sys_notice_detail, name='sys_notice_detail')
]
