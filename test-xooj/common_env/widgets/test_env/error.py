# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.error import Error


error = Error(
    INVALID_PARAMS = _('x_invalid_parameters'),
    ENV_NOT_EXIST = _('x_scene_not_exist'),
    USER_NOT_EXIST = _('x_user_not_exist'),

    FULL_ENV_CAPACITY=_('x_num_scenes_full'),
    FULL_PERSONAL_ENV_CAPACITY=_('x_num_personal_scenes_full'),
    TEST_ENV_EXIST = _('x_test_scene_have_existed'),
    TEST_ENV_NOT_EXIST = _('x_test_scene_not_existed'),
    CREATE_TEST_ENV_ERROR = _('x_create_test_scenario_failure'),
    DELETE_TEST_ENV_ERROR = _('x_del_test_scenario_failure'),
)

