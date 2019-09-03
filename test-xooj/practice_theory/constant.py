# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TheoryResError = enum(
    REQUIRED_FIELD=_('x_required_field'),
    TYPE_USEING=_('x_cannot_del_type'),
    LENFTH_TOO_LONG=_("x_options_1024"),
    UPLOAD_FORMAT_ERROR=_("x_upload_format_error"),
    SELECT_TASK_EVENT=_("x_select_task_event_category"),
    FORMAT_ERROR=_("x_format_error"),
    ACCURATE_FORMAT_ERROR=_("x_accurate_format_error"),
    ACCURATE_FORMAT_ERROR_NO_COL=_("x_accurate_format_error_no_col"),
    CURRENT_TASK_IS_EMPTY=_("x_current_topic_is_empty"),
    TOPIC_UP_OPTION=_("x_the_topic_option_is_up_to_8"),
    INCONSISTENT_ANSWERS_AND_OPTIONS=_("x_inconsistent_answers_and_options"),
)

CONSTANTTYPE=enum(
    SINGLE_CHOICE_QUESTION=_('x_single_choice'),
    MULTIPLE_CHOICE_QUESTION=_("x_multiple_choice"),
    JUDGMENT_CHOICE_QUESTION=_("x_judgment_problem")
)

SourceType = enum(
    QUESTION_BANK = 1,
    HOMEWORK = 2
)