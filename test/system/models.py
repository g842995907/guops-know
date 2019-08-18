# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from base.utils.enum import Enum
from base.utils.models.manager import MManager
from base_auth.models import User
from system.constant import Status

VersionStatus = Enum(
    FAIL=1,
    SUCCESS=2,
)


class UpgradeVersion(models.Model):
    upgrade_package = models.FileField(upload_to='upgrade')
    info = models.TextField(default='')
    create_time = models.DateTimeField(auto_now_add=True)
    upgrade_status = models.PositiveIntegerField(default=VersionStatus.SUCCESS)
    version = models.CharField(max_length=20, default='version')
    status = models.IntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    class Meta:
        db_table = 'system_upgrade_info'


class SystemConfiguration(models.Model):
    key = models.CharField(max_length=200)
    value = models.CharField(null=True, max_length=500)


class OperationLog(models.Model):
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT)
    module = models.PositiveIntegerField(default=0)

    # 操作类型
    OType = Enum(
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

    SyslogLevel = Enum(
        INFO=0,
        WARN=1,
        SEVERE=2,
    )
    level = models.PositiveIntegerField(default=SyslogLevel.INFO)

    LogStatus = Enum(
        SUCCESS=0,
        FAIL=1,
        PARTIAL_SUCCESS=2,
        OPERATING=3,
    )
    log_status = models.PositiveIntegerField(default=Status.NORMAL)
