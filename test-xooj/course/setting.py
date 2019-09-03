# -*- coding: utf-8 -*-

from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

from course.course_init import course_init

from system_configuration.utils import init_database
from x_person.utils.product_type import get_edition

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_course'),
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-book',
            },
            'CMS_AD_SHOW': False,
        },
        {
            'name': _('x_course_management'),
            'parent': _("x_course"),
            'href': 'course',
            'CMS_AD_SHOW': False,
        },
        {
            'name': _('x_course_schedule'),
            'parent': _("x_course"),
            'href': 'schedule_list',
            'CMS_AD_SHOW': False,
            'SHOW_FUNC': get_edition,
        },
        {
            'name': _('x_learning_statistics'),
            'parent': _("x_course"),
            'href': 'class_statistics_list',
            'CMS_AD_SHOW': False,
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_course'),
            'parent': None,
            'href': 'list'
        },
    ),
    'SLUG': 'course',
    'NODE_PATH': '/usr/bin/node',
    'RELY_ON': [
    ],
    'WEB_AD_SHOW': False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('COURSE', None, DEFAULTS, IMPORT_STRINGS)

from common_env.setting import api_settings as common_env_api_settings
from . import get_using_env_lessons, get_ignored_using_env_count, get_env_target_lesson

common_env_api_settings.GET_USING_ENV_OBJECTS_FUNCS.add(get_using_env_lessons)
common_env_api_settings.GET_IGNORED_USING_ENV_COUNT_FUNCS.add(get_ignored_using_env_count)
common_env_api_settings.GET_ENV_TARGET_FUNCS.add(get_env_target_lesson)

init_database.register_init_function('course', course_init)

from common_remote.setting import api_settings as common_remote_api_settings
from .utils.recording.callback import callback as recording_callback
common_remote_api_settings.RECORDING_CONVERT_CALLBACK.update(recording_callback)
