# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

CourseResError = enum(
    REQUIRED_FIELD=_('x_required_field'),
    COURSE_HAVE_EXISTED=_('x_course_already_exists'),
    VIDEO_IS_CHANGE=_('x_video_is_transcoding'),
    NOT_FOUND_JSTREE=_("x_no_parent_node_found"),
    JSTREE_IS_EMPTY=_("x_jstree_data_is_empty"),
    NO_ORDER=_("x_no_order_rule"),
    CANNT_CHANGE_HAS_DONE=_("x_exam_has_done"),
    LESSON_TYPE_WRONG=_("x_lesson_type_wrong"),
    LESSON_ENV_NOT_EXIST=_("x_used_lesson_env_not_exist"),
    NO_CONNECT_IDS=_("x_no_connect_ids"),
    NO_CONNECT_USERS=_("x_no_connect_users"),
    NO_LESSON_SELECTED=_("x_no_lesson_selected"),
    NO_LESSON_QUESTIONS=_("x_no_lesson_questions"),
    EXERCISE_HAS_DONE=_("x_exercise_has_done"),
    SCHEDULE_START_TIME_ERROR=_("x_end_gt_start_time"),
    SCHEDULE_TIME_ERROR=_("x_schedule_time_outside"),
    BUILTIN_CAN_NOT_EDIT=_("x_builtin_not_edit"),
    LOST_COURSE=_('x_lost_course'),
    LOST_LESSON=_('x_lost_lesson'),
    LOST_CLASSES=_('x_lost_classes'),
    LOST_START=_('x_lost_start'),
    LOST_END=_('x_lost_end'),
    CLASS_IN_SCHEDULES=_('x_class_in_schedules')
)

VIDEOSTATE = enum(
    NOVIDEO=0,
    SUCCESS=1,
    CHANGEING=2,
    FAIL=3,
)

COURSESTATE = enum(
    ABNORMAL=0,
    NORMAL=1
)


ReportStatus = enum(
    PASS=1,
    NOT_PASS=0
)
