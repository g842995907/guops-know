# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_framework.utils.rest.routers import get_default_router

from .cms import api
from .cms import views


viewsets = (
    api.ActiveEnvViewSet,
    api.EnvViewSet,
    api.StandardDeviceViewSet,
    api.EnvAttackerViewSet,
)
router = get_default_router(viewsets)

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'^active_env_list/$', views.active_env_list, name='active_env_list'),
    url(r'^env_list/$', views.env_list, name='env_list'),
    url(r'^env_list/(?P<pk>[0-9]+)/$', views.env_detail, name='env_detail'),
    url(r'^env_attacker_list/$', views.env_attacker_list, name='env_attacker_list'),
    url(r'^env_attacker_list/(?P<pk>[0-9]+)/$', views.env_attacker_detail, name='env_attacker_detail'),
    url(r'^standard_device_list/$', views.standard_device_list, name='standard_device_list'),
    url(r'^standard_device_list/(?P<pk>[0-9]+)/$', views.standard_device_detail, name='standard_device_detail'),

    url(r'^share_teacher/(?P<event_id>[a-z0-9]+)/$', views.share_teacher, name='share_teacher'),
    url(r'^share_standard_device_teacher/(?P<event_id>[a-z0-9]+)/$', views.share_standard_device_teacher, name='share_standard_device_teacher'),
    url(r'^dump_env_data/$', views.dump_env_data, name='dump_env_data'),
]


from .widgets import urls as widgets_urls

urlpatterns += [
    url(r'^widgets/', include(widgets_urls, namespace='widgets')),
]