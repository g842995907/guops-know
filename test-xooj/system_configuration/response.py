# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

BACKUP = enum(
    DUMP_FAIL=_('x_backup_failed'),
    LOAD_FAIL=_('x_import_failed'),
)

CAPTCHA = enum(
    CAPTCHA_WRONG=_('x_verification_code_error'),
)

SysNoticeError = enum(
    REQUIRED_FIELD=_('x_required_field'),
    NAME_TO_LONG=_('x_title_too_long'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    CONTENT_TO_LONG=_('x_content_too_long'),
    PLEASE_SELECT_CLASSES=_('x_select_class'),
    PLEASE_SELECT_FACULTY=_('x_select_department'),
    PLEASE_SELECT_MAJOR=_('x_select_grade'),
    PLEASE_SELECT_FORMAT=_("x_please_choose_format"),
    LOST_TITLE=_('x_lost_title'),
    LOST_CONTENT=_('x_lost_content'),
    CONTENTLT100=_('x_content_length_lt_100'),
)