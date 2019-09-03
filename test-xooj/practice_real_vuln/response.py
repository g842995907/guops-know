# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

TaskResError = enum(
    TITLE_TO_LONG=_('x_title_too_long'),
    TITLE_HAVE_EXISTED=_('x_title_already_exists'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    INVALID_PARAMS=_('x_invalid_parameters'),
    NO_ENV_CONF=_('x_sence_setting'),
    NO_ENV_FILE=_('x_no_environmental_documents'),
    NO_ENV_CONF_FILE=_('x_file_missing_scene_configuration'),
    INVALID_ENV_CONF_FILE=_('x_invalid_scene_configuration'),
    NO_FLAGS=_('x_lack_flag'),
    REQUIRED_FIELD=_('x_required_field'),
    SCORE_TO_BIG=_('x_score_2000'),
    SCORE_TYPE=_('x_score_type_error'),
    SCORE_TO_SMALL=_("x_score_small"),
    REPEAT=_("x_name_have_existed"),
    ANSWER_REPEAT=_("x_flag_repeat"),
    SCORE_FIELD=_("x_score_field_required"),
    EVN_CRROR=_("x_answer_env_error"),
    FLAGS_ERROR=_("x_flag_error_new"),
    FLAGS_REPEAT=_("x_flag_repeat")
)


CONSTANTTYPE = enum(
    ANALYSIS_QUESTIONS=_("x_analysis_questions"),
    OPERATION_QUESTIONS=_("x_operation_questions")
)

