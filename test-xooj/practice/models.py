# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from common_auth.models import User
from common_auth.models import Classes
from common_framework.models import ShowLock, Builtin, AuthAndShare
from common_framework.utils.models.manager import MyManager
from common_resource.base.model import Resource

from practice import resource
from practice.constant import TaskEventStatus


class TaskEvent(Resource, ShowLock, Builtin, AuthAndShare):
    name = models.CharField(max_length=50, default='')
    status = models.PositiveIntegerField(default=TaskEventStatus.NORMAL, null=True)
    logo = models.ImageField(upload_to='image', null=True, default=None)
    last_edit_time = models.DateTimeField(default=timezone.now)
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='last_edit_user')
    weight = models.PositiveIntegerField(default=10)
    create_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='create_user')
    type = models.PositiveIntegerField(default=3)
    public = models.BooleanField(default=False)
    objects = MyManager({'status': TaskEventStatus.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name

    ResourceMeta = resource.TaskEventMeta


class PracticeSubmitSolved(models.Model):
    class Meta:
        unique_together = (('submit_user', 'task_hash'),)

    submit_user = models.ForeignKey(User, on_delete=models.CASCADE)
    submit_time = models.DateTimeField(default=timezone.now)
    submit_answer = models.TextField(default=None, null=True)

    score = models.PositiveIntegerField(default=0)
    weight_score = models.FloatField(default=0)

    is_solved = models.BooleanField(db_index=True, default=True)
    task_hash = models.CharField(max_length=100, null=True)
    type = models.PositiveIntegerField(default=0)


class PracticeSubmitLog(models.Model):
    submit_user = models.ForeignKey(User, on_delete=models.CASCADE)
    submit_time = models.DateTimeField(default=timezone.now)
    submit_answer = models.CharField(max_length=500, null=True)
    task_hash = models.CharField(max_length=100, null=True)
    type = models.PositiveIntegerField(default=0)
