from __future__ import unicode_literals

import uuid

from django.db import models

from common_auth.models import User, Classes
from common_framework.utils.constant import Status
from common_framework.utils.enum import enum

from practice.api import get_task_detail


class Direction(models.Model):
    cn_name = models.CharField(max_length=50, unique=True)
    en_name = models.CharField(max_length=50, default=None, null=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.cn_name

    class Meta:
        db_table = 'practice_experiment_category'


def experiment_hash():
    return "{}.experiment".format(uuid.uuid4())


class Experiment(models.Model):
    difficulty = enum(
        INTRUDCTION=0,
        INCREASE=1,
        EXPERT=2
    )

    name = models.CharField(max_length=200)
    direction = models.ForeignKey(Direction, null=True, on_delete=models.SET_NULL)
    logo = models.FileField(upload_to='experiment/logo', null=True, default=None)
    introduction = models.TextField(null=True, blank=True)
    hash = models.CharField(max_length=100, null=True, default=experiment_hash)
    difficulty = models.PositiveIntegerField(default=difficulty.INTRUDCTION)
    pdf = models.FileField(upload_to='experiment/pdf', null=True)
    video = models.FileField(upload_to='experiment/video', null=True)
    practice = models.CharField(max_length=200, null=True)
    public = models.BooleanField(default=True)
    creater = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, related_name='experiment_creater')
    last_edit_user = models.ForeignKey(User, on_delete=models.SET_NULL,
                                       null=True, related_name='experiment_last_edit_user')
    auth_classes = models.ManyToManyField(Classes)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.name

    def practice_name(self):
        if not self.practice:
            return ""
        try:
            hash, type_id = self.practice.split(".")
            if type_id:
                task_detail = get_task_detail(type_id, self.practice)
                return task_detail.get("title_dsc")
        except Exception, e:
            return self.practice
