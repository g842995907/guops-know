# -*- coding: utf-8 -*-
from django.conf import settings

from common_framework.utils.constant import Edition
from common_framework.utils.license import get_system_config


def get_product_type():
    return 0


def get_edition():
    if not settings.DEBUG:
        if not get_system_config('edition'):
            return 1
        else:
            edition = int(get_system_config('edition'))
            if edition == Edition.PROFESSION:
                return 1
            if edition == Edition.EDUCATION:
                return 0
    return 0
