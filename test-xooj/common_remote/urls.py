# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from common_remote import views


urlpatterns = [
    url(r'^api/connection/(?P<connection_id>[0-9]+)/info/$', views.connection_info, name='connection_info'),
    url(r'^api/connection/(?P<connection_id>[0-9]+)/enable_recording/$', views.enable_recording, name='enable_recording'),
    url(r'^api/connection/(?P<connection_id>[0-9]+)/disable_recording/$', views.disable_recording, name='disable_recording'),
    url(r'^api/recording_convert/$', views.recording_convert, name='recording_convert'),
    url(r'^api/recording_convert/(?P<task_id>[0-9]+)/over/$', views.recording_convert_over, name='recording_convert_over'),
    url(r'^api/login_guacamoles/$', views.login_guacamoles, name='login_guacamoles'),
]
