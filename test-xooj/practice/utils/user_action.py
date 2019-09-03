# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.enum import enum
from system_configuration.utils.user_action import get_ua


UATemplate = enum(
    PRACTICE_TASK=_('练习题目：{type}/{task}'),
)

ua = get_ua(UATemplate)