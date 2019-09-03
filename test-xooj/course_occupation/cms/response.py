# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum


OCCUPATION_ERROR = enum(
    REPEAT_ADDITION=_('x_repeat_addition')
)