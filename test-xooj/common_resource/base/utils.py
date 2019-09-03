# -*- coding: utf-8 -*-

from django.utils.module_loading import import_string
from django.utils import six


# 如果是字符串尝试import
def try_import(cls):
    if isinstance(cls, six.string_types):
        return import_string(cls)
    return cls