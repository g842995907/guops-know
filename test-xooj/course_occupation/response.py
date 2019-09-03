# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

OccupationError = enum(
    NAME_REQUIRED=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    SYSTEM_NOT_MODIFIED=_('x_not_edited_system'),
    SYSTEM_NOT_DELETE=_('x_not_deleted_system'),
    SYSTEM_MODIFIED_PUBLIC=_('x_not_executed_system'),
    TIME_INDEX_ERROR=_('x_time_error_index_notexist'),
    OCCUPATION_IS_USING_BY_USER=_('x_the_user_using_occupaitons'),
    OCCUPATION_IS_NOT_EXIST=_('x_profession_does_not_exist'),
    OCCUPATION_ONT_CHOICE=_('x_no_occupation_choice'),
)
