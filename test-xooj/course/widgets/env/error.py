# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.error import Error


error = Error(
    NO_PERMISSION = _('x_no_operation_permissions'),

    LESSON_ENV_EXIST = _('x_scene_have_existed'),
    FULL_ENV_CAPACITY = _('x_num_scenes_full'),
    FULL_PERSONAL_ENV_CAPACITY = _('x_num_personal_scenes_full'),
    LESSON_ENV_NOT_CONFIGURED = _('x_topic_scene_not_configured'),
    LESSON_ENV_NOT_EXIST = _('x_scene_not_exist'),
    DELAY_LESSONENV_ERROR = _('x_failed_extend_scene'),

    INVALID_PARAMS = _('x_invalid_parameters'),
    LESSON_NOT_EXIST = _('x_class_hours_not_exist'),
    CREATE_LESSON_ENV_ERROR = _('x_failed_create_scene'),
    DELETE_LESSON_ENV_ERROR = _('x_failed_delete_scene'),
    TEAM_NOT_EXIST = _('x_team_not_exist'),
    USER_NOT_EXIST = _('x_user_not_exist'),
)
