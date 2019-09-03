# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TaskCategoryError = enum(
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    REPEAT=_("x_name_have_existed"),
    TYPE_USEING=_('x_cannot_del_type'),
)
