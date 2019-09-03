# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from common_auth.models import User
from common_framework.utils.enum import enum
from common_framework.utils.constant import Status
from common_framework.utils.models.manager import MyManager
from common_framework.models import Builtin
from course.models import Course


# 职业体系
class OccupationSystem(Builtin):
    Difficult = enum(
        FIRSTLEVEL=1,
        SECONDLEVEL=2,
        THIRDLEVEL=3,
        FOURTHLEVEL=4,
    )

    name = models.CharField(max_length=100)
    describe = models.TextField(null=True, blank=True)
    difficulty = models.PositiveIntegerField(default=Difficult.FIRSTLEVEL)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'course_occupation_system'
        ordering = ['-create_time', '-update_time']

    class MyMeta:
        _builtin_modify_field = ['public', 'id']


class OccupationLink(models.Model):
    occupation = models.ForeignKey(OccupationSystem, related_name='occupation')  # 本身职位
    advanced = models.ForeignKey(OccupationSystem, related_name='advanced', null=True)  # 进阶职位
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return self.advanced

    class Meta:
        db_table = 'course_occupation_link'


# 职业课程
class OccupationCourse(models.Model):
    Difficulty = enum(
        BASICS=0,
        ADVANCED=1,
        SENIOR=2
    )
    occupation_system = models.ForeignKey(OccupationSystem, related_name='occu_sys')
    course = models.ForeignKey(Course, related_name='occu_course')
    stage = models.PositiveIntegerField(default=Difficulty.BASICS)
    obligatory = models.BooleanField(default=True)

    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return self.course.name

    class Meta:
        db_table = 'course_occupation_course'
        ordering = ['-create_time', '-update_time']


# 用户选择职业
class OccupationIsChoice(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='occupation_user')
    occupation = models.ForeignKey(OccupationSystem, null=True, on_delete=models.SET_NULL,
                                   related_name='occupation_choice')

    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return self.occupation.name

    class Meta:
        db_table = 'course_occupation_ischoice'

    pass
