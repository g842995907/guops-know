# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from django.utils.translation import ugettext_lazy as _

from django.db import models
from django.utils import timezone

from common_auth.models import User, Classes, Faculty, Major
from common_framework.utils.constant import Status
from common_framework.utils.enum import enum
from common_framework.models import ShowLock, Builtin, AuthAndShare
from common_framework.utils.models.manager import MyManager
from common_env.models import Env, WaitingCreatePool
from common_resource.base.model import Resource

from practice.api import get_task_detail

from course import resource
from course.constant import VIDEOSTATE
from practice_capability.models import TestPaper


class AbstractDirection(Resource, models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, related_name='child')

    class Meta:
        abstract = True


class Direction(AbstractDirection):
    cn_name = models.CharField(max_length=200)
    en_name = models.CharField(max_length=200)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.cn_name

    class Meta:
        db_table = 'course_category'

    ResourceMeta = resource.DirectionMeta


def course_hash():
    return "{}.course".format(uuid.uuid4())


def lesson_hash():
    return "{}.lesson".format(uuid.uuid4())


class Course(Resource, ShowLock, Builtin, AuthAndShare):
    # 课程难度
    Difficulty = enum(
        INTRUDCTION=0,
        INCREASE=1,
        EXPERT=2
    )
    name = models.CharField(max_length=200)
    direction = models.ForeignKey(Direction, null=True,
                                  on_delete=models.SET_NULL,
                                  related_name='direction')
    sub_direction = models.ForeignKey(Direction, null=True,
                                      on_delete=models.SET_NULL,
                                      related_name='sub_direction')
    logo = models.FileField(upload_to='course/logo', null=True, default=None)
    introduction = models.TextField(null=True, blank=True)
    course_writeup = models.TextField(null=True)
    difficulty = models.PositiveIntegerField(default=Difficulty.INTRUDCTION)
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, related_name='course_creater')
    last_edit_user = models.ForeignKey(User, null=True,
                                       on_delete=models.SET_NULL,
                                       related_name='course_last_edit_user')
    hash = models.CharField(max_length=100, null=True, default=course_hash)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.name

    class Meta:
        db_table = 'course_course'
        verbose_name = _('x_course')

    ResourceMeta = resource.CourseMeta


class LessonEnv(Resource, models.Model):
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True, default=None)
    Type = enum(
        SHARED=0,
        PRIVATE=1,
        GROUP=2,
    )
    type = models.IntegerField(default=Type.PRIVATE)
    destroy_delay = models.IntegerField(default=2)
    destroy_time = models.DateTimeField(default=None, null=True)
    # 正在共享的用户
    shared_users = models.ManyToManyField(User, related_name='lesson_env_shared_users')
    # 小组用户
    group_users = models.ManyToManyField(User, related_name='lesson_env_group_users')

    ResourceMeta = resource.LessonEnvMeta


class Lesson(Resource, Builtin, models.Model):
    # 课时类型
    Type = enum(
        THEORY=0,
        EXPERIMENT=1,
        PRACTICE=2,
        EXAM=3,
    )
    # 课程难度
    Difficulty = enum(
        INTRUDCTION=0,
        INCREASE=1,
        EXPERT=2
    )
    HTML_TYPE = enum(
        NEITHER=0,
        MD=1,
        PPT=2
    )
    # 选修/必修
    LESSON_TYPE = enum(
        NOT_CONFIGURED=0,
        ELECTIVE=1,
        REQUIRED=2
    )
    testpaper = models.ForeignKey(TestPaper, null=True, on_delete=models.SET_NULL, related_name='to_lesson')
    course = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    type = models.PositiveIntegerField(default=Type.THEORY)
    pdf = models.FileField(upload_to='course/pdf', null=True)
    html = models.FileField(upload_to='course/html', null=True)
    html_type = models.PositiveIntegerField(default=HTML_TYPE.NEITHER)
    video = models.FileField(upload_to='course/video', null=True)
    attachment = models.FileField(upload_to='course/attachment', null=True)
    practice = models.CharField(max_length=200, null=True)
    homework = models.CharField(max_length=200, null=True)
    env = models.CharField(max_length=200, null=True)
    difficulty = models.PositiveIntegerField(default=Difficulty.INTRUDCTION)
    hash = models.CharField(max_length=100, null=True, default=lesson_hash)
    public = models.BooleanField(default=True)
    lesson_type = models.PositiveIntegerField(default=LESSON_TYPE.NOT_CONFIGURED)
    exercise_public = models.BooleanField(default=False)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    order = models.IntegerField(default=9999)
    duration = models.IntegerField(default=0)
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, related_name='lesson_creater')
    markdown = models.TextField(null=True, blank=True)
    markdownfile = models.FileField(upload_to='course/markdownfile', null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    knowledges = models.CharField(max_length=1024, null=True)

    envs = models.ManyToManyField(LessonEnv)

    # 添加转换视频状态， 添加转换视频存储路径, 10*10转换比例
    video_state = models.PositiveIntegerField(default=VIDEOSTATE.NOVIDEO)
    video_scale = models.CharField(max_length=10, null=True, blank=True)
    video_change = models.FileField(upload_to='course/video_trans/video_change', null=True, max_length=800)
    video_preview = models.FileField(upload_to='course/video_trans/preview', null=True, max_length=200)
    video_poster = models.FileField(upload_to='course/video_trans/poster', null=True, max_length=200)

    def __unicode__(self):
        return '%s' % self.name

    class Meta:
        db_table = 'course_lesson'

    def practice_name(self):
        if not self.practice:
            return ""
        try:
            hash, type_id = self.practice.split(".")
            if type_id:
                task_detail = get_task_detail(type_id, self.practice, backend=True)
                return task_detail.get("title_dsc")
        except Exception, e:
            return self.practice

    def homework_name(self):
        if not self.homework:
            return ""
        try:
            hash, type_id = self.homework.split(".")
            if type_id:
                task_detail = get_task_detail(type_id, self.homework, backend=True)
                return task_detail.get("title_dsc")
        except Exception, e:
            return self.homework

    ResourceMeta = resource.LessonMeta


class LessonPaperTask(Resource, models.Model):
    Type = enum(
        PRACTICE=2,
        EXAM=3,
        EXERCISE=4,
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    type = models.PositiveIntegerField(default=Type.PRACTICE)
    task_hash = models.CharField(max_length=500)
    score = models.FloatField()

    class Meta:
        db_table = 'course_lesson_papertask'

    ResourceMeta = resource.LessonPaperTaskMeta


class LessonPaperRecord(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    task_hash = models.CharField(max_length=500)
    answer = models.CharField(max_length=500)
    solved = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    submit_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "course_lesson_paperecord"


class LessonJstree(Resource, models.Model):
    Type = enum(
        DEFAULT=0,
        FOLDER=1,
        FILE=2,
    )
    self_id = models.CharField(max_length=50)  # 记录jstree的id lesson+id 根id course+id
    course = models.ForeignKey(Course, null=True, blank=True, related_name='course_child')
    lesson = models.ForeignKey(Lesson, null=True, blank=True, related_name='lesson_child')
    parent = models.CharField(max_length=50, default="#")
    parents = models.CharField(max_length=100, default="#")
    text = models.CharField(max_length=200)
    type = models.PositiveIntegerField(default=Type.DEFAULT)  # 创建文件类型
    # state = models.CharField(max_length=200, null=True, blank=True)  # 节点属性json格式字符串
    public = models.BooleanField(default=True)  # 默认公开
    order = models.PositiveIntegerField(default=0)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    original_objects = MyManager({'public': False})

    class Meta:
        db_table = 'course_lesson_jstree'
        unique_together = ('self_id', "course")

    def __unicode__(self):
        return self.text

    ResourceMeta = resource.LessonJstreeMeta


class Record(models.Model):
    Progress = enum(
        LEARNING=1,
        LEARED=2
    )
    lesson = models.ForeignKey(Lesson, null=True,
                               on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True,
                             on_delete=models.SET_NULL,
                             related_name='record_user')
    pdf_progress = models.FloatField(default=0)
    video_progress = models.FloatField(default=0)
    progress = models.PositiveIntegerField(default=Progress.LEARNING)
    markdown_schedule = models.FloatField(default=0)
    study_time = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_learning_record'
        unique_together = ('user', "lesson")


class CourseSchedule(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    course = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    lesson = models.ForeignKey(Lesson, null=True, on_delete=models.SET_NULL)
    faculty = models.ForeignKey(Faculty, null=True, on_delete=models.SET_NULL)
    major = models.ForeignKey(Major, null=True, on_delete=models.SET_NULL)
    classes = models.ForeignKey(Classes, null=True, on_delete=models.SET_NULL)
    create_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    dow = models.CharField(default=None, max_length=64)

    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)


class ClassroomGroupInfo(models.Model):
    classroom = models.ForeignKey(CourseSchedule)
    # [{
    #     'key': unique_key,
    #     'users': group_user_ids,
    #     'lesson_env': lesson_env_id,
    # }]
    groups = models.TextField(default='[]')
    waits = models.ManyToManyField(WaitingCreatePool)


class ClassroomGroupTemplate(models.Model):
    classes = models.ForeignKey(Classes)
    name = models.CharField(max_length=100, default='')
    groups = models.TextField(default='[]')
    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)


class ScheduleSign(models.Model):
    course_schedule = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE)
    # 签到
    sign_in = models.BooleanField(default=False)
    sign_in_time = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    # 协助
    need_help = models.BooleanField(default=False)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)


class CourseUserStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, default=None)
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, default=None)
    experiment_seconds = models.PositiveIntegerField(default=0)
    experiment_update_time = models.DateTimeField(default=timezone.now)

    attend_class_seconds = models.PositiveIntegerField(default=0)
    attend_update_time = models.DateTimeField(default=timezone.now)
