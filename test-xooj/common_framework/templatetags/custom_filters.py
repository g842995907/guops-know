# -*- coding: utf-8 -*-
import re

from django import template
from django.template.defaultfilters import date
from django.utils import dateparse
from django.utils import timezone


register = template.Library()


@register.filter(expects_localtime=True, is_safe=False)
def cus_date(value, arg=None):
    try:
        parsed_datetime = dateparse.parse_datetime(value)
        parsed_datetime = timezone.localtime(parsed_datetime)
        return date(parsed_datetime, arg)
    except:
        return ''
