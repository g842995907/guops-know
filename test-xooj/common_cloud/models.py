from __future__ import unicode_literals

from django.db import models

from common_framework.utils.constant import Status
from common_framework.utils.enum import enum


class Department(models.Model):
    name = models.CharField(max_length=50)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    ip = models.GenericIPAddressField(null=True, default=None)
    public_key = models.FileField(null=True, default=None, upload_to='key')
    private_key = models.FileField(null=True, default=None, upload_to='key')
    license_info = models.CharField(max_length=1024, default=None, null=True)

    def __unicode__(self):
        return '%s' % self.name


class UpdateInfo(models.Model):
    name = models.CharField(max_length=50)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    zip = models.FileField(null=True, default=None, upload_to='update')
    create_time = models.DateTimeField(auto_now=True)
    change_log = models.CharField(max_length=1024)

    auto_update = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s' % self.name


class LicenseConfig(models.Model):
    cn_name = models.CharField(max_length=50)
    en_name = models.CharField(max_length=100)
    ConfigType = enum(
        CHAR=0,
        INT=1,
        TIME=2,
        SELECT=3,
    )
    type = models.PositiveIntegerField(default=ConfigType.CHAR)
