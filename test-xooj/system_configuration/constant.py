# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from common_framework.utils.enum import enum

GroupType = enum(
    ALL=0,
    TEACHER=1,
    STUDENT=2,
)

UserStatus = enum(
    DELETE=0,
    NORMAL=1,
)

NoticeType = enum(
    SYSNOTICE=0,
    SYSMESSAGE=1,
    TEAMMESSAGE=2,
    SCHEDULEMESSAGE=3,
    EVENTMESSAGE=4,
    USERMESSAGE=5,
)
