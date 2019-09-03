# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from common_framework.utils.enum import enum

TeamStatus = enum(
    DELETE=0,
    NORMAL=1,
    FIRED=2,
    FORBID=3
)

TeamUserStatus = enum(
    DELETE=0,
    JOIN=1,
    REFUSE=2,
    INVITE=3,
    EXIT=4,
    NEED_JOIN=5,
    NOT_EXIST=6,
)

UserStatus = enum(
    DELETE=0,
    NORMAL=1,
)

GroupType = enum(
    ADMIN=1,
    TEACHER=2,
    USER=3
)

InvitationStatus = enum(
    INVITATION=0,
    HASINVITATION=1,
    JOINED=2,
)