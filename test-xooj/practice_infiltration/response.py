# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TaskResError = enum(
    TITLE_TO_LONG=_('x_title_too_long'),
    TITLE_HAVE_EXISTED=_('x_title_already_exists'),
    INVALID_PARAMS=_('x_invalid_parameters'),
    NO_ENV_CONF=_('x_sence_setting'),
    NO_ENV_FILE=_('x_no_environmental_documents'),
    NO_ENV_CONF_FILE=_('x_file_missing_scene_configuration'),
    INVALID_ENV_CONF_FILE=_('x_invalid_scene_configuration'),
    NO_FLAGS=_('x_lack_flag'),
    REQUIRED_FIELD=_('x_required_field'),
    TYPE_USEING=_('x_cannot_del_type'),
    ANSWER_REPEAT=_("x_flag_repeat"),
    SCORE_FIELD=_("x_score_field_required"),
    SCORE_TO_SMALL=_("x_score_small"),
    SCORE_TO_BIG=_('x_score_2000'),
    EVN_CRROR=_("x_answer_env_error"),
    SOLVING_MODE=_("x_select_solution_mode"),
    FLAGS_ERROR=_("x_flag_error")
)


CONSTANTTYPE = enum(
    ANALYSIS_QUESTIONS=_("x_analysis_questions"),
    OPERATION_QUESTIONS=_("x_operation_questions")
)
