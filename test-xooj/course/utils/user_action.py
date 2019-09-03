# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.enum import enum
from system_configuration.utils.user_action import get_ua


UATemplate = enum(
    LEARN_COURSE=_('学习课程：{course}/{lesson}'),
)

ua = get_ua(UATemplate)