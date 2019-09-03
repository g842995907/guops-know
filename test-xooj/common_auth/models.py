# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.base_session import AbstractBaseSession
from django.contrib.sessions.models import Session, SessionManager
from django.db import models

# 院系、地区
from django.utils import timezone

from common_auth.constant import TeamStatus, TeamUserStatus
from common_framework.utils.constant import Status
from common_framework.utils.enum import enum
from common_framework.utils.models.manager import MyManager


class Faculty(models.Model):
    name = models.CharField(max_length=50)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name


# 年级、部门
class Major(models.Model):
    name = models.CharField(max_length=50)
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name


# 班级、项目组
class Classes(models.Model):
    name = models.CharField(max_length=50)
    major = models.ForeignKey(Major, on_delete=models.PROTECT)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name

    def major_name(self):
        return self.major.name

    def faculty(self):
        return self.major.faculty.id

    def faculty_name(self):
        return self.major.faculty.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_logo', null=True)
    status = models.PositiveIntegerField(default=TeamStatus.NORMAL)
    token = models.CharField(max_length=33, default=None, null=True)
    create_time = models.DateTimeField(default=timezone.now)
    modify_time = models.DateTimeField()
    brief_introduction = models.TextField(null=True)

    def __unicode__(self):
        return '%s' % self.name


class User(AbstractUser):
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, default=None, null=True)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, default=None, null=True)
    classes = models.ForeignKey(Classes, on_delete=models.SET_NULL, default=None, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, default=None, null=True)
    student_id = models.CharField(max_length=100, null=True, default=None)  # 学号、工号
    logo = models.ImageField(upload_to='user_logo', null=True, default=None)
    nickname = models.CharField(max_length=100, null=True)
    mobile = models.CharField(max_length=16, null=True, default=None)
    address = models.CharField(max_length=80, null=True, default=None)
    ID_number = models.CharField(max_length=40, null=True, default=None)
    brief_introduction = models.TextField(null=True)
    # 邮箱验证
    email_validate = models.BooleanField(default=False)
    # 用户过期时间
    expired_time = models.DateTimeField(null=True, blank=True)
    # 上次登录时间
    last_login_ip = models.CharField(max_length=100, null=True, default=None)

    USER = enum(
        DELETE=0,
        NORMAL=1,
        NEW_REGISTER=2,
        PASS=3,
        EXPIRED=4,
        DISABLED=5,
    )
    status = models.PositiveIntegerField(default=USER.NORMAL)
    Online = enum(
        OFFLINE=0,
        ONLINE=1,
    )
    report_time = models.DateTimeField(null=True, blank=True)
    total_online_time = models.PositiveIntegerField(default=0)


# 队伍成员表
class TeamUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status = models.PositiveIntegerField(default=TeamUserStatus.INVITE)
    has_handle = models.BooleanField()
    create_time = models.DateTimeField(default=timezone.now)
    modify_time = models.DateTimeField(default=timezone.now)
    team_leader = models.BooleanField(default=False)


# 邀请拒绝消息
class TeamUserNotice(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    has_notice = models.BooleanField()
    content = models.CharField(max_length=1024)
    create_time = models.DateTimeField()
    modify_time = models.DateTimeField()


class XSession(Session):
    ip = models.CharField(max_length=100, null=True, default=None)

    objects = SessionManager()

    @classmethod
    def get_session_store_class(cls):
        from common_framework.utils.x_sessionStore import SessionStore
        return SessionStore

    class Meta(AbstractBaseSession.Meta):
        db_table = 'x_django_session'
