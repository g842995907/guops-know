# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

ExamResError = enum(
    WARN_MESSAGES_1=_('x_end_greater_start'),
    WARN_MESSAGES_2=_('x_edit_exam_end_time'),
    WARN_MESSAGES_3=_('x_edit_not_start_time'),
    WARN_MESSAGES_4=_('x_exam_start_greater_current_time'),
    WARN_MESSAGES_5=_('x_exam_end_greater_current_time'),
    WARN_MESSAGES_6=_('x_start_time_fields_required'),
    WARN_MESSAGES_7=_('x_edit_exam_start_time'),
    WARN_MESSAGES_8=_('x_exam_name_not_empty'),
    WARN_MESSAGES_9=_("x_exams_name_already_exists"),
    NO_EXAM_QUESTIONS=_("x_no_exam_questions"),
    NOT_FOUND_EXAM=_("x_not_found_exam"),
    CANNT_CHANGE_HAS_DONE=_("x_exam_has_done"),
    TESTPAPER_ABNORMAL=_("x_testpaper_abnormal"),
)