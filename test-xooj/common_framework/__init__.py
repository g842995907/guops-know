# -*- coding: utf-8 -*-
import logging
from importlib import import_module

import six
from django.conf import settings
from django.core.cache import cache

from common_framework.x_setting.menu import menu
from common_framework.views import collect_menu_conf

__version__ = '1.1.1'

cms_root_menu = menu()
web_root_menu = menu()

logger = logging.getLogger()


def get_cache_menu(cms=False):
    slug = 'cms' if cms else 'web'
    data = cache.get('sys_%s_menu' % slug)
    if data:
        return data

    else:
        clear_menu()
        return menu()


def set_cache_menu(root_menu, cms=False):
    slug = 'cms' if cms else 'web'
    cache.set('sys_%s_menu' % slug, root_menu)


def _is_show_menu(app_setting, cms):
    pt = settings.PLATFORM_TYPE
    select_string = "{}_{}_SHOW".format("CMS" if cms else "WEB", pt)
    if hasattr(app_setting, select_string):
        show = getattr(app_setting, select_string)
        if show == False or show == 0:
            return False

    return True


def collect_menu(app_setting):
    try:
        cms_app_menu = app_setting.MENU
        web_app_menu = app_setting.WEB_MENU

        slug = app_setting.SLUG

        if _is_show_menu(app_setting, cms=True):
            collect_menu_conf(cms_app_menu, cms_root_menu, slug, cms=True)

        if _is_show_menu(app_setting, cms=False):
            collect_menu_conf(web_app_menu, web_root_menu, slug)

    except Exception, e:
        raise e


def check_rely_on(app_name, app_setting):
    from collections import Iterable

    rely_on = app_setting.RELY_ON
    if rely_on and isinstance(rely_on, Iterable):
        for r in rely_on:
            if not isinstance(r, six.string_types):
                logger.error("app[%s] rely on error, it require string[app_name]", app_name)

            if r not in settings.XCTF_APPS:
                logger.error("app[%s] rely on %s, but it not exist", app_name, r)
                raise Exception("app[%(name)s] rely on [%(app)s], but it not exist"
                                % {'name': app_name, 'app': r})


def get_menu():
    for app in settings.XCTF_APPS:
        setting_path = '%s.%s' % (app, 'setting')
        try:
            _app_conf = import_module(setting_path)
            app_settings = _app_conf.api_settings
            if not app_settings:
                continue

            collect_menu(app_settings)

            check_rely_on(app, app_settings)

        except Exception, e:
            logger.error("app[%] error collect_menu or check_rely_on", app)
            raise e


def clear_menu():
    setattr(web_root_menu, '_sub', [])
    setattr(cms_root_menu, '_sub', [])
