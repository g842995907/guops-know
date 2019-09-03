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
)
