# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class MyManager(models.Manager):
    def __init__(self, iexclude=None, ifilter=None):
        super(MyManager, self).__init__()
        self._inner_exclude = iexclude
        self._inner_filter = ifilter

    def get_queryset(self):
        queryset = super(MyManager, self).get_queryset()
        if self._inner_exclude:
            queryset = queryset.exclude(**self._inner_exclude)
        if self._inner_filter:
            queryset = queryset.filter(**self._inner_filter)
        return queryset
