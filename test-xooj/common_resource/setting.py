# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.conf import settings

from common_framework.x_setting.settings import APISettings


DEFAULTS = {
    'MENU': (
    ),
    'WEB_MENU': (
    ),
    'SLUG': 'common_resource',
    'RELY_ON': [
    ],

    'DUMP_TMP_DIR': os.path.join(settings.BASE_DIR, 'common_resource', 'resources/dump_tmp'),
    'LOAD_TMP_DIR': os.path.join(settings.BASE_DIR, 'common_resource', 'resources/load_tmp'),
    'COURSE_README': os.path.join(settings.BASE_DIR, 'common_resource', 'resources/readme/course_readme.md'),
    'PRACTICE_README': os.path.join(settings.BASE_DIR, 'common_resource', 'resources/readme/practice_readme.md'),
    'VIDEO_TRANS': os.path.join(settings.MEDIA_ROOT, 'course', 'video_trans/video_change'),
    'ZIP_PWD': '2386f2849c35b4f5a8f269b3b422bb38',
    'DEFAULT_USER_ID': 1,
}

IMPORT_STRINGS = ()

api_settings = APISettings('common_resource', None, DEFAULTS, IMPORT_STRINGS)

