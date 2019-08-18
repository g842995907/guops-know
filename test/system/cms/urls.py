# -*- coding: utf-8 -*-
from django.conf.urls import url

from system.cms import api
from system.cms import views

viewsets = (
    api.UpgradeVersionViewSet,
    api.SystemConfigurationViewSet,
    api.RunLogViewSet,
    api.OperationLogViewSet,
)

apiurlpatterns = [
    url(r'^license/$', views.get_license, name='license'),
    url(r'^run_log_level/$', views.run_log_level, name='run_log_level'),
    url(r'^down_log/$', views.down_log, name='down_log'),
    url(r'^get_instance_list/$', views.get_instance_list, name='get_instance_list'),
]
