# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TaskResError = enum(
    INVALID_ENV=_('x_invalid_scene'),
    PLEASE_SELECT_ENV=_('x_please_select_scene'),
    NO_TASK_ENV=_('x_lack_environmental_information'),
    NO_FLAGS=_('x_lack_flag'),
    REQUIRED_FIELD=_("x_required_field"),
    FIELD_LENGTH_REQUIRED=_("x_length_not_greater_30"),
    PARAMETER_ERROR=_("x_parameter_error"),
    HAS_ALL_ANSWER=_("x_has_all_answered")
)

TaskCategoryError = enum(
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
)
