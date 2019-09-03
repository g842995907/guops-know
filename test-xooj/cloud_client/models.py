from __future__ import unicode_literals

from django.db import models

from common_framework.utils.constant import Status as b_status
from common_framework.utils.enum import enum


class UpdateInfo(models.Model):
    status = models.PositiveIntegerField(default=b_status.NORMAL)
    encrypt_file = models.FileField(upload_to='update')
    create_time = models.DateTimeField(auto_now=True)

    Status = enum(
        UPDATE_UN_START=0,
        UPDATE_START=1,
        UPDATE_OK=2,
        UPDATE_FAIL=3,
    )
    update_status = models.PositiveIntegerField(default=Status.UPDATE_UN_START)
    change_log = models.CharField(max_length=1024, null=True)

