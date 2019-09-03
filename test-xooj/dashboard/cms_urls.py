# -*- coding: utf-8 -*-
from django.conf.urls import url

from dashboard.cms import views


urlpatterns = [
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^platform_stats/$', views.platform_stats, name='platform_stats'),

    url(r'^get_alarm/$', views.get_alarm, name='get_alarm'),
    url(r'^hyperv_stats/$', views.hyperv_stats, name='hyperv_stats'),
    url(r'^system_stats/$', views.system_stats, name='system_stats'),
    url(r'^get_system_state/$', views.get_system_state, name='get_system_state'),

    url(r'^get_hyper_list/$', views.get_hyper_list, name='get_hyper_list'),
    url(r'^online_user_monitor/$', views.online_user_monitor, name='online_user_monitor')
]
