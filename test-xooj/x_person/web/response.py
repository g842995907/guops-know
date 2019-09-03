# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.enum import enum

ResError = enum(
    HAVE_APPLIED=_('x_applied_please_patient'),
    HAVE_INVITED=_('x_invite_please_patient'),
    METHODNOTALLOWED=_('x_method_not_allowed'),

    TEAM_NOT_EXIST=_('x_team_not_exist'),

    TIME_FORMAT_WRONG=_("x_tram_time_wrong"),

    USER_HAVE_TEAM=_('x_user_already_exists'),

    ORIGIN_PASSWORD_WRONG=_('x_initial_password_wrong'),

    Invalid_Para=_('x_invaild_symbol'),

    NEW_PASSWORD_WRONG=_('x_password_claim'),

    EMAIL_WRONG=_('x_email_format_wrong'),

    MOBILE_WRONG=_('x_phone_format_wrong'),

    TYPE_USEING=_('x_cannot_del_type'),

    TaskEvent_USEING=_('x_cannot_del_problem_sets'),

    Other_TaskEvent_USEING=_('x_cannot_del_shared_problem_sets'),

    FAIL_DELETE=_('x_failed_delete'),

)
