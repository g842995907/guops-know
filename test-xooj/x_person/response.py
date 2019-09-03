# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

ORGANIZATON = enum(
    TITLE_HAVE_EXISTED=_('x_name_have_existed'),
    CHILDREN_EXISTED=_('当前目录下存在子节点'),
    CLASSES_HAVE_STUDENT=_('班级下面存在用户，请先删除用户'),
)

USERINFO = enum(
    USERNAME_HAVE_EXISTED=_('x_name_have_existed'),
    FORMAT_WRONG=_('x_username_format_error'),
    USERNAME_TO_LONG=_('用户名过长'),
    EMAIL_HAVE_EXISTED=_('邮箱已存在'),
    EMAIL_HAVE_WARG=_('邮箱格式错误'),
    REALNAME_TO_LONG=_('姓名过长'),
    STUDENT_ID_TO_LONG=_('号码过长'),
    STUDENT_WARG=_('号码格式错误'),
    PASSWORD_NO_FORMAT=_('密码8～20位<br>且必须包含大小写字母数字及特殊字符'),
    NO_AUTHORITY=_('x_no_authority')
)

TEAM = enum(
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    ALREADY_TEAM=_("x_already_in_team"),
    PLEASE_CHOOSE_TEAM_TO_DISBAND=_('x_please_choose_a_team_to_disband'),
    YOU_ARE_NOT_IN_THE_TEAM_AND_CANNOT_DISSMISS_ANY_TEAM=_('x_you_are_not_in_the_team_and_cannot_dismiss_any_team'),
    CAN_ONLY_DISBAND_HIS_TEAM=_('x_can_only_disband_his_team'),
    ONLY_THE_CAPTAIN_CAN_DISBAND_THE_TEAM=_("x_only_the_captain_can_disband_the_team"),
    TEAM_LEADER_USER_DOES_NOT_EXIST=_("x_team_leader_user_does_not_exist"),
    TEAM_NOT_FOUND=_('x_not_found_team'),
    NOW_TIME_ERROE=_("x_not_greater_current_time"),
)

FILE = enum(
    FILE_FORMAT_ERROR=_('文件格式不正确'),
    FILE_READ_ERROR=_('文件读取失败'),
    FILE_NOT_EXISTS=_('文件不存在'),
)

REGEX = enum(
    REGEX_USER=_(u'^[0-9a-zA-Z\-_]{6,14}$'),
    REGEX_PASSWORD=_(u'^(?![A-Za-z0-9]+$)(?![a-z0-9\\W]+$)(?![A-Za-z\\W]+$)(?![A-Z0-9\\W]+$)^.{8,20}$'),
    # REGEX_PASSWORD=_(u'^.{8,20}$'),
    REGEX_MOBILE=_("^0\d{2,3}[ \-]+?\d{7,8}$|^1[358]\d{9}$|^147\d{8}$|^176\d{8}$"),
    REGEX_EMAIL=_('[0-9a-zA-Z][\w\.-]+@(?:[A-Za-z0-9]+\.)+(com|cn|gov|net|org)$'),
)


OccupationError = enum(
    NAME_REQUIRED=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_have_existed'),
    SYSTEM_NOT_MODIFIED=_('x_not_edited_system'),
    SYSTEM_NOT_DELETE=_('x_not_deleted_system'),
    SYSTEM_MODIFIED_PUBLIC=_('x_not_executed_system'),
    TIME_INDEX_ERROR=_('x_time_error_index_notexist'),
    OCCUPATION_IS_USING_BY_USER=_('x_the_user_using_occupaitons'),
    NOT_FOUND_USER=_("x_not_found_user"),
    NOT_FOUND_TEAM=_("x_not_found_team"),
)

ExportUserError = enum(
    EXPORT_ERROR=_('x_export_user_error_response')
)

# echarts气泡图标，生成使用原始数据, 列表顺序不可切换
bubbleOption_data_30 = [
        [0, 0, "None"],
        [1, 0, "None"],
        [2, 0, "None"],
        [3, 0, "None"],
        [4, 0, "None"],
        [5, 0, "None"],
        [6, 0, "None"],
        [7, 0, "None"],
        [8, 0, "None"],
        [9, 0, "None"],
        [10, 0, "None"],
        [11, 0, "None"],
        [12, 0, "None"],
        [13, 0, "None"],
        [14, 0, "None"],
        [15, 0, "None"],
        [16, 0, "None"],
        [17, 0, "None"],
        [18, 0, "None"],
        [19, 0, "None"],
        [20, 0, "None"],
        [21, 0, "None"],
        [22, 0, "None"],
        [23, 0, "None"],
        [24, 0, "None"],
        [25, 0, "None"],
        [26, 0, "None"],
        [27, 0, "None"],
        [28, 0, "None"],
        [29, 0, "None"],
]