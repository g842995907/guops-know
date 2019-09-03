# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

PracticeResError = enum(
    WARN_MESSAGES_6=_("x_test_already_exists"),
    WARN_MESSAGES_7=_("x_testpaper_cannot_empty"),
    WARN_MESSAGES_8=_('x_exam_name_not_empty'),
    WARN_MESSAGES_9=_("x_exams_name_already_exists"),
    NO_EXAM_QUESTIONS=_("x_no_exam_questions"),
    NOT_FOUND_EXAM=_("x_not_found_testpaper"),
    CANNT_CHANGE_HAS_DONE=_("x_exam_has_done"),
)

TestpaperType = enum(
    SINGLE=0,
    MULTIPLE=1,
    JUDGMENT=2,
    OPERATION=3
)

AppType = enum(
    THEROY=0,
    REAL_VULN=1,
    EXERCISE=2,
    ATTACK_DEFENCE=4,
    INFILTRSTION=5
)
