# -*- coding: utf-8 -*-
from django.utils.module_loading import import_string


def get_app_name(obj):
    return obj.__module__.split('.')[0]


def get_app_settings(obj):
    app_name = get_app_name(obj)
    settings_string = '%s.setting.api_settings' % app_name
    return import_string(settings_string)
