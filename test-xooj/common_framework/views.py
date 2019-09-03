# -*- coding: utf-8 -*-
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext, ugettext
from rest_framework import exceptions

from common_framework import menu


def find_menu(slug="", cms=False):
    def _find_menu(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            import common_framework
            web_menus = common_framework.get_cache_menu().sub_menu
            if 0 == len(web_menus):
                common_framework.get_menu()
                common_framework.set_cache_menu(common_framework.web_root_menu, cms=False)
                common_framework.set_cache_menu(common_framework.cms_root_menu, cms=True)

            if cms:
                menus = common_framework.get_cache_menu(cms=True).sub_menu
                if not args[0].user.is_superuser:
                    filter_system_manager = ugettext('x_system_management')
                    menus = filter(lambda x: x.name.encode('utf-8') != filter_system_manager, menus)
            else:
                menus = common_framework.get_cache_menu(cms=False).sub_menu

            menu = {
                'menu': menus,
                'active_menus': slug
            }
            kwargs['menu'] = menu

            return fun(*args, **kwargs)

        return wrapper

    return _find_menu


def _is_show_signle_menu(menu, cms):
    pt = settings.PLATFORM_TYPE
    select_string = "{}_{}_SHOW".format("CMS" if cms else "WEB", pt)
    show = menu.get(select_string, None)
    if show is not None:
        if not show or show == 0:
            return False

    return True


def _is_show_func(menu):
    show_func = menu.get('SHOW_FUNC', None)
    if show_func is not None:
        cache.clear()
        return show_func()

    return False


def collect_menu_conf(app_menu, root_menu, slug, cms=False):
    if app_menu is not None and type(app_menu) == tuple:
        for m in app_menu:
            if not _is_show_signle_menu(m, cms):
                continue

            if _is_show_func(m):
                continue

            parent = m.get('parent', None)
            name = m.get('name', 'N/A')
            icon = m.get('icon', None)
            href = m.get('href', None)

            new_menu = menu()
            new_menu.icon = icon
            new_menu.name = name

            if not href:
                new_menu.href = None
            else:
                if href.find("http") == 0:
                    new_menu.href = href
                elif href.find("/") == 0:
                    new_menu.href = href
                else:
                    if cms:
                        new_menu.href = u'/%s/%s/%s' % (settings.ADMIN_SLUG, slug, href)
                    else:
                        new_menu.href = u'/%s/%s' % (slug, href)

            if parent is not None:
                menu_parent = root_menu.find(parent)
            else:
                menu_parent = root_menu

            menu_parent.sub_menu.append(new_menu)


def exception_handler(exc, context):
    from rest_framework.views import exception_handler as base_exception_handler
    response = base_exception_handler(exc, context)
    if isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, (list, dict)):
            data = exc.get_full_details()
        else:
            data = {'detail': exc.get_full_details()}
        response.data = data

    return response
