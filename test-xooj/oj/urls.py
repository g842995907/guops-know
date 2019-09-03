# -*- coding: utf-8 -*-
"""cyberpeace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import logging
import os
from importlib import import_module

from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.views.static import serve

from common_cms import views as cms_views
from common_framework.utils.load_app import App
from common_web import views as web_views
from oj import settings
from django.conf.urls import handler404, handler403

logger = logging.getLogger(__name__)
from django.views.i18n import javascript_catalog

js_info_dict = {
    'packages': ('x_i18n', 'event', 'event_attack_defense', 'event_infiltration', 'event_exam',
                 'practice', 'practice_capability',
                 'dashboard', 'course', 'x_person',
                 'common_env', 'x_tools', 'common_cloud', 'system_configuration',
                 'common_web', 'x_vulns', 'practice_attack_defense',
                 'practice_real_vuln', 'practice_man_machine', 'practice_exercise',
                 'course_occupation',
                 ),
}

urlpatterns = [
    url(r'^%s/' % settings.ADMIN_SLUG, include('common_cms.urls', namespace='common_cms')),
    url(r'', include('common_web.urls', namespace='common_web')),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), cms_views.media),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    url(r'^accounts/login/$', auth_views.login, {'template_name': 'web/login.html'}, name='login'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
]


# 为每一个模块添加url路由
for app in settings.XCTF_APPS + settings.BASE_APPS:
    _app = App(app, urlpatterns)
    _app.load_url()


handler404 = web_views.not_found
handler403 = web_views.forbidden
