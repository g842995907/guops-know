# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.utils import timezone

from common_auth.models import User
from common_framework.utils.constant import Status
from common_framework.utils.enum import enum
from common_framework.utils.models.manager import MyManager
from common_auth.models import Classes, Major, Faculty


class SystemConfiguration(models.Model):
    DesktopTransmissionQuality = enum(
        LOW='1',
        MIDDLE='2',
        HIGH='3',
    )
    key = models.CharField(max_length=200)
    value = models.CharField(null=True, max_length=500)


class Backup(models.Model):
    creater = models.ForeignKey(User, on_delete=models.PROTECT)
    create_time = models.DateTimeField(default=timezone.now)
    backup_name = models.CharField(null=True, max_length=128)
    Status = enum(
        DELETED=0,
        CREATING=1,
        DONE=2,
        FAIL=3,
    )
    status = models.PositiveIntegerField(default=Status.CREATING)
    LoadStatus = enum(
        CREATING=1,
        DONE=2,
        FAIL=3,
    )
    migrate_time = models.DateTimeField(default=None, null=True)
    load_status = models.PositiveIntegerField(default=LoadStatus.CREATING)
    objects = MyManager({'status': Status.DELETED})
    original_objects = models.Manager()


class SysLog(models.Model):
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, null=True, default=None)
    title = models.CharField(null=True, max_length=128)
    content = models.CharField(null=True, max_length=1024)

    SyslogLevel = enum(
        INFO=0,
        WARN=1,
        SEVERE=2,
    )
    level = models.IntegerField(default=SyslogLevel.INFO)

    LogStatus = enum(
        SUCCESS=0,
        FAIL=1,
        PARTIAL_SUCCESS=2,
    )
    log_status = models.PositiveIntegerField(default=Status.NORMAL)


class OperationLog(models.Model):
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT)
    module = models.PositiveIntegerField(default=0)

    # 操作类型
    OType = enum(
        CREATE=0,
        UPDATE=1,
        DELETE=2,
    )
    operation_type = models.PositiveIntegerField(default=OType.CREATE)

    # 操作对象id
    operation_obj = models.PositiveIntegerField(default=0)

    # 操作对象str，一般为title，name属性
    operation_str = models.CharField(default=None, null=True, max_length=512)


    # 详细内容
    content = models.CharField(null=True, max_length=10240)

    SyslogLevel = enum(
        INFO=0,
        WARN=1,
        SEVERE=2,
    )
    level = models.PositiveIntegerField(default=SyslogLevel.INFO)

    LogStatus = enum(
        SUCCESS=0,
        FAIL=1,
        PARTIAL_SUCCESS=2,
        OPERATING=3,
    )
    log_status = models.PositiveIntegerField(default=Status.NORMAL)


class SysNotice(models.Model):
    name = models.CharField(max_length=64)
    content = models.TextField(null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    last_edit_time = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, null=True, related_name='notice_creator',on_delete=models.SET_NULL)

    Group = enum(
        ALL=0,
        TEACHER=1,
        STUDENT=2,
        SELECT=3,
    )
    group = models.PositiveIntegerField(null=True, default=Group.ALL)

    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, default=None, null=True)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, default=None, null=True)
    classes = models.ForeignKey(Classes, null=True, default=None)

    notified_person = models.ForeignKey(User, null=True, default=None)

    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    Type = enum(
        SYSNOTICE=0,
        SYSMESSAGE=1,
        TEAMMESSAGE=2,
        SCHEDULEMESSAGE=3,
        EVENTMESSAGE=4,
        USERMESSAGE=5,
    )
    type = models.PositiveIntegerField(default=Type.SYSNOTICE)


class UserNotice(models.Model):
    sys_notice = models.ForeignKey(SysNotice, null=True, default=None)
    user = models.ForeignKey(User, null=True, default=None)

    Status = enum(
        DELETE=0,
        READ=1,
        IGNORE=2,
    )
    status = models.PositiveIntegerField(default=Status.READ)
    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()


class UserAction(models.Model):
    time = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.CharField(default='', max_length=10240)
    extra = models.TextField(default='')


