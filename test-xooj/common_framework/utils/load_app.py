# -*- coding: utf-8 -*-
import logging
import os
from importlib import import_module

from django.conf import settings
from django.conf.urls import include, url

from common_framework import _is_show_menu

logger = logging.getLogger(__name__)

class App(object):

    def __init__(self, app, urlpatterns):
        self.app = app
        self.urlpatterns = urlpatterns

    def update_urlpatterns(self, app_name, app_setting):
        slug = getattr(app_setting, 'SLUG', None)
        if slug is None:
            return

        full_url_path = get_exist_path([
            os.path.join(settings.BASE_DIR, app_name, 'urls.py'),
            os.path.join(settings.BASE_DIR, app_name, 'urls.so'),
        ])
        if full_url_path:
            urls_path = '%s.urls' % app_name
            try:
                if _is_show_menu(app_setting, cms=False):
                    __import__(urls_path)
                    self.urlpatterns.append(url(r'^%s/' % slug, include(urls_path, namespace=slug)))
            except Exception as e:
                logger.info("[%s] errormsg[%s] urls", app_name, str(e))

        full_cms_url_path = get_exist_path([
            os.path.join(settings.BASE_DIR, app_name, 'cms_urls.py'),
            os.path.join(settings.BASE_DIR, app_name, 'cms_urls.so'),
        ])
        if full_cms_url_path:
            cms_urls_path = '%s.cms_urls' % app_name
            try:
                if _is_show_menu(app_setting, cms=True):
                    __import__(cms_urls_path)
                    self.urlpatterns.append(
                        url(r'^%s/%s/' % (settings.ADMIN_SLUG, slug), include(cms_urls_path, namespace='cms_%s' % slug)))
            except Exception as e:
                logger.info("[%s] errormsg[%s] cms urls", app_name, str(e))

    def load_url(self):
        full_setting_path = get_exist_path([
            os.path.join(settings.BASE_DIR, self.app, 'setting.py'),
            os.path.join(settings.BASE_DIR, self.app, 'setting.so'),
        ])
        if full_setting_path:
            setting_path = '%s.%s' % (self.app, 'setting')

            try:
                _app_conf = import_module(setting_path)
                app_settings = _app_conf.api_settings
                if not app_settings:
                    return

                self.update_urlpatterns(self.app, app_settings)
            except Exception as e:
                logger.info("load url error error[%s]", str(e))
                raise e


def get_exist_path(paths):
    for path in paths:
        if os.path.exists(path):
            return path

    return None
